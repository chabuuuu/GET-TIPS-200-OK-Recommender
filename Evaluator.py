from pyspark.ml.evaluation import RegressionEvaluator
import numpy as np

class Evaluator:
    def __init__(self, model, ratings, k=10):
        self.model = model
        self.ratings = ratings
        self.k = k

    def calculate_metrics(self, predictions):
        # Calculate MAE
        mae_evaluator = RegressionEvaluator(metricName="mae", labelCol="weight", predictionCol="prediction")
        mae = mae_evaluator.evaluate(predictions)

        rmse_evaluator = RegressionEvaluator(metricName="rmse", labelCol="weight",
                                    predictionCol="prediction")
        rmse = rmse_evaluator.evaluate(predictions)
        
        # Calculate HR, cHR, ARHR, Coverage, Diversity, Novelty
        user_recs = self.model.recommendForAllUsers(self.k).collect()
        
        hits = 0
        cumulative_hits = 0
        reciprocal_hits = 0
        total_recommendations = 0
        unique_recommendations = set()
        all_recommendations = []
        
        for user_rec in user_recs:
            user_id = user_rec['session_id_index']
            recommendations = user_rec['recommendations']
            user_ratings = predictions.filter(predictions['session_id_index'] == user_id).select('post_id_index', 'weight').collect()
            
            user_rated_items = set([row['post_id_index'] for row in user_ratings])
            
            for i, rec in enumerate(recommendations):
                post_id_index = rec['post_id_index']
                all_recommendations.append(post_id_index)
                unique_recommendations.add(post_id_index)
                
                if post_id_index in user_rated_items:
                    hits += 1
                    cumulative_hits += 1
                    reciprocal_hits += 1 / (i + 1)
            
            total_recommendations += len(recommendations)
        
        hr = hits / total_recommendations
        chr = cumulative_hits / total_recommendations
        arhr = reciprocal_hits / total_recommendations
        coverage = len(unique_recommendations) / self.ratings.select('post_id_index').distinct().count()
        diversity = len(set(all_recommendations)) / len(all_recommendations)
        novelty = np.mean([np.log2(1 + self.ratings.filter(self.ratings['post_id_index'] == post_id_index).count()) for post_id in unique_recommendations])
        
        print("Root-mean-square error = " + str(rmse))
        print(f"Mean Absolute Error (MAE) = {mae}")
        print(f"Hit Rate (HR) = {hr}")
        print(f"Cumulative Hit Rate (cHR) = {chr}")
        print(f"Average Reciprocal Hit Rate (ARHR) = {arhr}")
        print(f"Coverage = {coverage}")
        print(f"Diversity = {diversity}")
        print(f"Novelty = {novelty}")

        return mae, hr, chr, arhr, coverage, diversity, novelty