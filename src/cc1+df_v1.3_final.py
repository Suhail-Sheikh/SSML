from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql.context import SQLContext
from pyspark.sql.types import StructType
from pyspark.sql.types import *
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
import sys

bsize = int(sys.argv[1])

sc = SparkContext('local[2]','stream_test')
ssc = StreamingContext(sc, 1)
#sqlContext = SQLContext(sc)
spark=SparkSession.builder.appName('sparkdf').getOrCreate()

lines = ssc.socketTextStream("localhost", 6100)

def parseJson(rdd):
	if not rdd.isEmpty():
		df = spark.read.json(rdd)
		#df.printSchema()
		
		#df.createOrReplaceTempView("mytable")
		#df2 = spark.sql("SHOW COLUMNS FROM mytable")
		#df2.show()
		
		# So it is creating a table with col name as row no. in batch, and data as a json of the entire row
		# eg: if 5 records passed per batch,
		# col names: 	0	1	2	3	4
		# data:	row1	row2	row3	row4	row5
		# each row is a struct which further splits into the 3 features
		
		# TO FLATTEN (didn't work):
		#json_parsed = spark.read.json(df.rdd.map(lambda row: row.0))
		#json_parsed.printSchema()
		
		# TO FLATTEN (worked)
		batch_df = df.select(col("0.*")).withColumnRenamed('feature0','Subject').withColumnRenamed('feature1','Message').withColumnRenamed('feature2','Spam/Ham')
		for row_no in range(1, bsize):
			s = str(row_no)+".*"
			df3 = df.select(col(s)).withColumnRenamed('feature0','Subject').withColumnRenamed('feature1','Message').withColumnRenamed('feature2','Spam/Ham')
			batch_df = batch_df.union(df3)
			#duplicates removed
			batch_df.show(truncate=False)

lines.foreachRDD(lambda rdd: parseJson(rdd))

ssc.start()

print(ssc.getActive())

ssc.awaitTermination()

ssc.stop(True,True)

ssc.close()