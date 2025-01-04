from pyspark.sql import SparkSession

from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.sql import Row
from Evaluator import Evaluator
from PostLoad import PostLoad
from pyspark.ml.feature import StringIndexer


if __name__ == "__main__":

    spark = SparkSession\
    .builder\
    .appName("ALSExample")\
    .config("spark.driver.memory", "6g") \
    .config("spark.executor.cores", '5')\
    .getOrCreate()

    postMetadataPath="/home/haphuthinh/Workplace/School_project/do-an-1/Get-tips-200-ok-recommend/post.csv"
    
    postLoad = PostLoad(postMetadataPath)

    all_sessions_df = postLoad.get_all_sessions_data()

    # lines = spark.read.option("header", "true").csv("../ml-latest-small/ratings.csv").rdd

    # ratingsRDD = lines.map(lambda p: Row(userId=int(p[0]), movieId=int(p[1]),
    #                                      rating=float(p[2]), timestamp=int(p[3])))
    
    ratings = spark.createDataFrame(all_sessions_df)

    # Index session_id and post_id columns
    session_indexer = StringIndexer(inputCol="session_id", outputCol="session_id_index")
    post_indexer = StringIndexer(inputCol="post_id", outputCol="post_id_index")

    # Fit the indexers
    ratings = session_indexer.fit(ratings).transform(ratings)
    ratings = post_indexer.fit(ratings).transform(ratings)
    
    (training, test) = ratings.randomSplit([0.8, 0.2])

    als = ALS(maxIter=5, regParam=0.01, userCol="session_id_index", itemCol="post_id_index", ratingCol="weight",
              coldStartStrategy="drop")
    model = als.fit(training)


    userRecs = model.recommendForAllUsers(10)

    
    #user85Recs = userRecs.filter(userRecs['session_id'] == "9378998f-ec0f-4d96-9ad2-b711cdefad8e").collect()
    #user85Recs = userRecs.filter(userRecs['session_id'] == "9378998f-ec0f-4d96-9ad2-b711cdefad8e").collect()

    # Save the recommend for all user to redis
    for row in userRecs.collect():
                recommendations = row['recommendations']

                # Create a list to hold the post IDs
                post_ids = []
                for rec in recommendations:
                    original_post_id = ratings.filter(ratings['post_id_index'] == rec['post_id_index']).select('post_id').collect()[0]['post_id']
                    post_ids.append(original_post_id)

                original_session_id = ratings.filter(ratings['session_id_index'] == row.session_id_index).select('session_id').collect()[0]['session_id']

                postLoad.save_data_to_redis(key = original_session_id, values= post_ids)




    # Get the index of the specific session_id
    session_id_index = ratings.filter(ratings['session_id'] == "9378998f-ec0f-4d96-9ad2-b711cdefad8e").select('session_id_index').collect()[0]['session_id_index']

    # Filter recommendations for the specific user
    user85Recs = userRecs.filter(userRecs['session_id_index'] == session_id_index).collect()


        
    # for row in user85Recs:
    #     for rec in row.recommendations:


    #         print(postLoad.get_title_by_id(rec.post_id))

    for row in user85Recs:
        for rec in row.recommendations:
            # Convert numeric post_id back to string post_id]
            original_post_id = ratings.filter(ratings['post_id_index'] == rec.post_id_index).select('post_id').collect()[0]['post_id']
            # Get the title using the original string post_id
            print("Original post_id:", original_post_id)
            print(postLoad.get_title_by_id(original_post_id))

    spark.stop()
