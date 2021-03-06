# -*- coding: utf-8 -*-
"""Sparkify_done.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XygS0ECTtqVMI2NnQzbl1zta4InXT4Yp
"""

#!/usr/bin/env python
# coding: utf-8

from google.colab import drive
drive.mount('/content/drive')

"""# Sparkify Project Workspace<br>
This workspace contains a tiny subset (128MB) of the full dataset available (12GB). Feel free to use this workspace to build your project, or to explore a smaller subset with Spark before deploying your cluster on the cloud. Instructions for setting up your Spark cluster is included in the last lesson of the Extracurricular Spark Course content.<br>
<br>
You can follow the steps below to guide your data analysis and model building portion of this project.

**install libraries**
"""

# !pip uninstall pyspark
!pip install pyspark==3.0.0

"""**Import libraries**"""

# Commented out IPython magic to ensure Python compatibility.
# import libraries
from pyspark.sql import SparkSession      
import pyspark.sql.functions as psqf
import pyspark.sql.types as psqt
from pyspark.ml.feature import VectorAssembler, StandardScaler\

from pyspark.ml.classification import RandomForestClassifier
from pyspark.mllib.util import MLUtils

from pyspark.mllib.evaluation import BinaryClassificationMetrics
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml import Pipeline
from pyspark.ml.feature import IndexToString, StringIndexer, VectorIndexer

import datetime
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
# %matplotlib inline

"""**create a Spark session**"""

# create a Spark session
spark = SparkSession.builder.appName("customer-churn data pipeline").getOrCreate()

"""# Load and Clean Dataset<br>
In this workspace, the mini-dataset file is `mini_sparkify_event_data.json`. Load and clean the dataset, checking for invalid or missing data - for example, records without userids or sessionids. 
"""

#load json file using .read.json function 
data_path = "/content/drive/MyDrive/new_project/mini_sparkify_event_data.json"
user_event = spark.read.json(data_path)
df = user_event

"""**Dataset**"""

#print 1st line of json file.
user_event.show(5)

"""**shape of dataset**"""

print(user_event.count(), len(user_event.columns))

"""**Schema of dataset**"""

user_event.printSchema()

"""**Count missing values**"""

#count null values for each column
df_nulls = user_event.select([psqf.count(psqf.when(psqf.isnull(c), c)).alias(c) for c in user_event.columns])
df_nulls.show()

# let's make sure page column doesn't have nulls ( as we'll define churn on 'page' column). Do for userId too.
df_nulls.select('userId', 'page').show()

"""**There are two levels**"""

user_event.select('level').distinct().show()

"""**Value counts of level**"""

level_counts= user_event.groupby('level').agg({'level':'count'}).withColumnRenamed("count(level)", "level_count")
level_counts.show()

"""**Distint page**"""

user_event.select('page').distinct().show()

"""**Value counts of page**"""

page_counts= user_event.groupby('page').agg({'page':'count'}).withColumnRenamed("count(page)", "page_count")
page_counts.show()

"""Let's look at **Cancel** and **Cancellation Confirmation** samples in the dataset"""

cancel_events = user_event.filter(psqf.col('page').isin(['Cancel','Cancellation Confirmation'])).select(['userID','page', 'firstName', 'lastName','ts', 'auth'])
cancel_events.show(5, False)

cancel_reg_ids  = [vv['userID'] for vv in cancel_events.select('userID').collect()]
print(len(cancel_reg_ids), len(set(cancel_reg_ids)))

"""# Exploratory Data Analysis<br>
When you're working with the full dataset, perform EDA by loading a small subset of the data and doing basic manipulations within Spark. In this workspace, you are already provided a small subset of data you can explore.<br>
<br>
### Define Churn<br>
<br>
Once you've done some preliminary analysis, create a column `Churn` to use as the label for your model. I suggest using the `Cancellation Confirmation` events to define your churn, which happen for both paid and free users. As a bonus task, you can also look into the `Downgrade` events.<br>
<br>
### Explore Data<br>
Once you've defined churn, perform some exploratory data analysis to observe the behavior for users who stayed vs users who churned. You can start by exploring aggregates on these two groups of users, observing how much of a specific action they experienced per a certain time unit or number of songs played.

**Define dependent variable**
"""

churn_event = user_event.groupby('userId').agg(psqf.collect_list('page').alias('pages'))
# define 1 as churned, 0 otherwise
churn_f = psqf.udf(lambda x: 1 if 'Cancel' in set(x) else 0)
churn_event = churn_event.withColumn("label", churn_f(churn_event.pages)).drop('pages')

churn_event.show(5)

"""**Downgraded customers**"""

#customer who downgraded
downgrade_events = user_event.filter(psqf.col('page').isin(['Downgrade']))
downgrade_events.select(['userID','page', 'firstName', 'lastName','ts', 'auth']).show(5, False)

downgrade_reg_ids = [vv['userID'] for vv in downgrade_events.select('userID').collect()]
print(len(downgrade_reg_ids), len(set(downgrade_reg_ids)))

"""**Downgraded customer cancel their subscription**"""

# Now let's see which of those who downgraded also cancel thier subscription
down_cancel = set(cancel_reg_ids).intersection((set(downgrade_reg_ids)))
print('{0:.2f}% of customers who downgraded have also cancelled their subscriptions'.format(
    100*(len(down_cancel))/len(set(downgrade_reg_ids))))

user_event.filter((psqf.col('userID') == list(down_cancel)[0]) &
                  (psqf.col('page').isin(['Downgrade','Cancel']))).select(['userID','page', 'firstName','ts']).show()

labeled_df  = churn_event.join(user_event, 'userId')

labeled_df.filter(psqf.col('page').isin(["Cancel", "Cancellation Confirmation"])).select('userId', 'page', 'label').show(5)

"""**Value counts of label**"""

churned_count = labeled_df.groupby("label").count().show()

"""**Songs played users who stayed vs user who churn**"""

# compare songs played by users who stayed vs user who churn
songsplayed = labeled_df.where(psqf.col('song')!='null').groupby("label").agg(psqf.count(psqf.col('song')).alias('SongsPlayed'))
songsplayed.show(5)

"""**songs liked for users who stayed vs user who churn**"""

# number of songs liked for users who stayed vs user who churn
thumbsup_count = labeled_df.where((psqf.col('page')=='Thumbs Up')).groupby("label").agg(psqf.count(psqf.col('page')).alias('thumbsUpCount'))
thumbsup_count.show(5, False)

"""**song dislikes for users who stayed vs user who churn**"""

# number of dislikes for users who stayed vs user who churn
thumbsdown_count = labeled_df.where((psqf.col("page")=='Thumbs Down')).groupby("label").agg(psqf.count(psqf.col('page')).alias('thumbsDownCount'))
thumbsdown_count.show(5)

# number of downgrades for users who stayed vs user who churn
downgrade_count = labeled_df.where((psqf.col("page")=='Downgrade')).groupby("label").agg(psqf.count(psqf.col('page')).alias('downgradeCount'))
downgrade_count.show(5)

"""**EDA**"""

use_level_count = labeled_df.groupby('userId', 'level', 'label').count()
use_level_count_pd  = use_level_count.select("userId", "level", 'label').toPandas()
use_level_count_pd[['level', 'label']].groupby(['level', 'label']).agg({'label':'count'}).unstack().plot(kind='bar');
plt.title('churned-level customer count comparison')
plt.ylabel('customer count');

use_level_count_pd[['level', 'label']].groupby(['level', 'label']).agg({'label':'count'}).unstack().plot(kind='bar');
plt.title('churned-level customer count comparison')
plt.ylabel('customer count');

use_level_count_pd.label.value_counts().plot(kind='bar');
plt.ylabel('User count')
plt.xlabel('label')
plt.title('Churned vs active customer count');

"""# Feature Engineering<br>
Once you've familiarized yourself with the data, build out the features you find promising to train your model on. To work with the full dataset, you can follow the following steps.<br>
- Write a script to extract the necessary features from the smaller subset of data<br>
- Ensure that your script is scalable, using the best practices discussed in Lesson 3<br>
- Try your script on the full data set, debugging your script if necessary<br>
<br>
If you are working in the classroom workspace, you can just extract features based on the small subset of data contained here. Be sure to transfer over this work to the larger dataset when you work on your Spark cluster.

** Number of songs each user played**
"""

songsplayed = labeled_df.where(psqf.col('song')!='null').groupby("userId").agg(psqf.count(psqf.col('song')).alias('SongsPlayed')).orderBy('userId')
songsplayed.show(5)

"""**Number of distinct hour counts  a user logged in the system**"""

hours_udf = psqf.udf(lambda x: datetime.datetime.utcfromtimestamp(x/1000.0).strftime('%Y-%m-%d-%H'))
hours_df  = labeled_df.select('userId', 'ts').withColumn('hour', hours_udf(psqf.col('ts')))
hours_df.show(5)

hour_count_df = hours_df.where(psqf.col('userId')!='null').groupby('userId').agg((psqf.countDistinct(psqf.col('hour'))).alias("HourCount")).orderBy('userId')
hour_count_df.show(5)

"""### Thumbs Up and Thumbs Down counts:
A user having a lot of thumbs down could be an indication of the users disastisfaction with song recommendations from Sparkify while a more thumbs up ( likes) by a user indicates user is happy with song recommendations

**Filter rows where user-id is missing**
"""

# filter out rows with userId == null
labeled_df = labeled_df.where(psqf.col('userId')!='null')
labeled_df.show(5)

thumbsup_count = labeled_df.where((psqf.col('page')=='Thumbs Up') &(psqf.col('userId')!='null')).groupby("userId").agg(psqf.count(psqf.col('page')).alias('thumbsUpCount')).orderBy('userId')
thumbsup_count.show(5, False)

thumbsdown_count = labeled_df.where((psqf.col("page")=='Thumbs Down')&(psqf.col('userId')!='null')).groupby("userId").agg(psqf.count(psqf.col('page')).alias('thumbsDownCount')).orderBy('userId')
thumbsdown_count.show(5)

"""**Merge all features by vector assembler**"""

## Join all the features
features_df = churn_event.join(songsplayed, "userId").\
join(hour_count_df, "userId").join(thumbsup_count, "userId").join(thumbsdown_count, "userId")

features_df.show(5)

assembler = VectorAssembler(inputCols=["SongsPlayed", "HourCount", "thumbsUpCount", "thumbsDownCount"], outputCol="rawFeatures")
features_df = assembler.transform(features_df)
features_df.select('label', 'rawFeatures').show(4)

"""**Feature scaling**"""

scaler = StandardScaler(inputCol="rawFeatures", outputCol="features", withStd=True)
scalerModel = scaler.fit(features_df)
features_df = scalerModel.transform(features_df)

input_data = features_df.withColumn('label', psqf.col('label').cast(psqt.IntegerType())).select('label', 'features')
input_data.show(2)

"""# Modeling<br>
Split the full dataset into train, test, and validation sets. Test out several of the machine learning methods you learned. Evaluate the accuracy of the various models, tuning parameters as necessary. Determine your winning model based on test accuracy and report results on the validation set. Since the churned users are a fairly small subset, I suggest using F1 score as the metric to optimize.

**Handle categorical features using string indexer**
"""

# Index labels, adding metadata to the label column.
# Fit on whole dataset to include all labels in index.
labelIndexer = StringIndexer(inputCol="label", outputCol="indexedLabel").fit(input_data)

# Automatically identify categorical features, and index them.
# Set maxCategories so features with > 4 distinct values are treated as continuous.
featureIndexer =\
    VectorIndexer(inputCol="features", outputCol="indexedFeatures", maxCategories=4).fit(input_data)

"""**Train test spliting**"""

# Split the data into training and test sets (since dataset is imbalanced)
(trainingData, tempData) = input_data.randomSplit([0.6, 0.4])
(validationData, testData) = tempData.randomSplit([0.5, 0.5])

"""**Random Forest**"""

# Train a RandomForest model.
rf = RandomForestClassifier(labelCol="indexedLabel", featuresCol="indexedFeatures", numTrees=10)
# Convert indexed labels back to original labels.
labelConverter = IndexToString(inputCol="prediction", outputCol="predictedLabel",
                               labels=labelIndexer.labels)
# Chain indexers and forest in a Pipeline
pipeline = Pipeline(stages=[labelIndexer, featureIndexer, rf, labelConverter])

# Train model.  This also runs the indexers.
model = pipeline.fit(trainingData)

"""**Prediction on unseen data**"""

# Make predictions.
predictions = model.transform(validationData)

# Select example rows to display.
predictions.select("predictedLabel", "label", "features").show(5)

# Select (prediction, true label) and compute test error
evaluator = MulticlassClassificationEvaluator(
    labelCol="indexedLabel", predictionCol="prediction", metricName="accuracy")
accuracy = evaluator.evaluate(predictions)
print("Validation Error = %g" % (1.0 - accuracy))

rfModel = model.stages[2]
print(rfModel)  # summary only

"""**Evaluate the performance**"""

f1_score_evaluator = MulticlassClassificationEvaluator(labelCol="indexedLabel", predictionCol="prediction",metricName='f1')
f1_score = f1_score_evaluator.evaluate(predictions)
print("F1 score = %g" % (f1_score))

"""**Hyperparameter tunning of random forest**"""

rfc = RandomForestClassifier(labelCol="indexedLabel", featuresCol="indexedFeatures")
# Chain indexers and forest in a Pipeline
pipeline = Pipeline(stages=[labelIndexer, featureIndexer, rfc, labelConverter])
param_grid = ParamGridBuilder().addGrid(rfc.numTrees, [10, 15]).addGrid(rfc.maxDepth, [2, 5]).build()
cv = CrossValidator(estimator=pipeline, 
                    estimatorParamMaps = param_grid, 
                    evaluator = MulticlassClassificationEvaluator(metricName='f1'),
                    numFolds=3)

best_model = cv.fit(trainingData)

"""**Evaluate performance of optimized model**"""

def evaluate_model(model, data):
    """
    Make prediction and evaluate model.
    Parameters
    -----------
        model: model object
    returns
    -------
        None
    """
    predictions = model.transform(data)

    # Select example rows to display.
    predictions.select("predictedLabel", "label", "features").show(5)

    # Select (prediction, true label) and compute test error
    evaluator = MulticlassClassificationEvaluator(
        labelCol="indexedLabel", predictionCol="prediction", metricName="accuracy")
    accuracy = evaluator.evaluate(predictions)
    print("Error = %g" % (1.0 - accuracy))
    f1_score_evaluator = MulticlassClassificationEvaluator(labelCol="indexedLabel", predictionCol="prediction",metricName='f1')
    f1_score = f1_score_evaluator.evaluate(predictions)
    print("F1 score = %g" % (f1_score))

evaluate_model(model=best_model, data=validationData)

evaluate_model(model=best_model, data=testData)

"""# Results
We have analysed the sparkify dataset and come up with new features to predict churn. We then created a machine learning model and tuned it to improve its performance. We achieved an accuracy score of - and F1 score of - on the test dataset.

# Conclusion
We are able to achieve an accuracy score of -- and F1 score of -- on the test dataset using the tuned Random Forest algorithm. The model peformance can be further improved by creating additional features and includiding some of the features that I have left out for this analysis. The model should also be tested using samples from the left out big dataset which hasn't been used for this analysis. Once we are satified with the result, a large scale of the model can be implemented on the cloud.

# Final Steps<br>
Clean up your code, adding comments and renaming variables to make the code easier to read and maintain. Refer to the Spark Project Overview page and Data Scientist Capstone Project Rubric to make sure you are including all components of the capstone project and meet all expectations. Remember, this includes thorough documentation in a README file in a Github repository, as well as a web app or blog post.

**Load the dataset**
"""

data = spark.read.json(data_path)
df = data

"""**Dataset**"""

df.show(5)

"""**shape of dataset**"""

print(df.count(), len(df.columns))

"""**Schema of dataset**"""

df.printSchema()

"""**Count missing values**"""

#count null values for each column
df_nulls = df.select([psqf.count(psqf.when(psqf.isnull(c), c)).alias(c) for c in user_event.columns])
df_nulls.show()

# let's make sure page column doesn't have nulls ( as we'll define churn on 'page' column). Do for userId too.
df_nulls.select('userId', 'page').show()

"""**Levels**"""

df.select('level').distinct().show()

"""**Value counts of level**"""

level_counts= df.groupby('level').agg({'level':'count'}).withColumnRenamed("count(level)", "level_count")
level_counts.show()

"""**Distint value of  page**"""

df.select('page').distinct().show()

churn_event = df.groupby('userId').agg(psqf.collect_list('page').alias('pages'))
# define 1 as churned, 0 otherwise
churn_f = psqf.udf(lambda x: 1 if 'Cancel' in set(x) else 0)
churn_event = churn_event.withColumn("label", churn_f(churn_event.pages)).drop('pages')

churn_event.show(2)

"""**Exploratory Data Analysis**

**count comparison of customers churned-level**
"""

use_level_count = labeled_df.groupby('userId', 'level', 'label').count()
use_level_count_pd  = use_level_count.select("userId", "level", 'label').toPandas()
use_level_count_pd[['level', 'label']].groupby(['level', 'label']).agg({'label':'count'}).unstack().plot(kind='bar');
plt.title('churned-level customer count comparison')
plt.ylabel('customer count');

"""**Churned vs active customer count**"""

use_level_count_pd.label.value_counts().plot(kind='bar');
plt.ylabel('User count')
plt.xlabel('label')
plt.title('Churned vs active customer count');

"""**Label distribution**"""

labeled_df.groupBy('userId','label','gender').count().select('label', 'gender').groupBy('label','gender').count().show()

"""**Number of songs each user played**"""

songsplayed = labeled_df.where(psqf.col('song')!='null').groupby("userId").agg(psqf.count(psqf.col('song')).alias('SongsPlayed')).orderBy('userId')
songsplayed.show(5)

"""**Number of distinct hour counts  a user logged in the system**"""

hours_udf = psqf.udf(lambda x: datetime.datetime.utcfromtimestamp(x/1000.0).strftime('%Y-%m-%d-%H'))
hours_df  = labeled_df.select('userId', 'ts').withColumn('hour', hours_udf(psqf.col('ts')))
hours_df.show(5)

hour_count_df = hours_df.where(psqf.col('userId')!='null').groupby('userId').agg((psqf.countDistinct(psqf.col('hour'))).alias("HourCount")).orderBy('userId')
hour_count_df.show(5)

"""**Filter rows where user-id is missing**"""

# filter out rows with userId == null
labeled_df = labeled_df.where(psqf.col('userId')!='null')
labeled_df.show(5)

thumbsup_count = labeled_df.where((psqf.col('page')=='Thumbs Up') &(psqf.col('userId')!='null')).groupby("userId").agg(psqf.count(psqf.col('page')).alias('thumbsUpCount')).orderBy('userId')
thumbsup_count.show(5, False)

thumbsdown_count = labeled_df.where((psqf.col("page")=='Thumbs Down')&(psqf.col('userId')!='null')).groupby("userId").agg(psqf.count(psqf.col('page')).alias('thumbsDownCount')).orderBy('userId')
thumbsdown_count.show(5)

"""# **Feature engineering**

**Merge all features using vector assembler**
"""

## Join all the features
features_df = churn_event.join(songsplayed, "userId").\
join(hour_count_df, "userId").join(thumbsup_count, "userId").join(thumbsdown_count, "userId")

features_df.show(5)

"""**Vector Assembler**"""

assembler = VectorAssembler(inputCols=["SongsPlayed", "HourCount", "thumbsUpCount", "thumbsDownCount"], outputCol="rawFeatures")
features_df = assembler.transform(features_df)
features_df.select('label', 'rawFeatures').show(4)

"""**Feature scaling**"""

scaler = StandardScaler(inputCol="rawFeatures", outputCol="features", withStd=True)
scalerModel = scaler.fit(features_df)
features_df = scalerModel.transform(features_df)

input_data = features_df.withColumn('label', psqf.col('label').cast(psqt.IntegerType())).select('label', 'features')
input_data.show(2)

"""**Handle categorical features**"""

# Index labels, adding metadata to the label column.
# Fit on whole dataset to include all labels in index.
labelIndexer = StringIndexer(inputCol="label", outputCol="indexedLabel").fit(input_data)

# Automatically identify categorical features, and index them.
# Set maxCategories so features with > 4 distinct values are treated as continuous.
featureIndexer =\
    VectorIndexer(inputCol="features", outputCol="indexedFeatures", maxCategories=4).fit(input_data)

"""#**Modeling**

**Train test splitting**
"""

# Split the data into training and test sets (since dataset is imbalanced)
(trainingData, tempData) = input_data.randomSplit([0.6, 0.4])
(validationData, testData) = tempData.randomSplit([0.5, 0.5])

"""**Random Forest**"""

# Train a RandomForest model.
rf = RandomForestClassifier(labelCol="indexedLabel", featuresCol="indexedFeatures", numTrees=10)
# Convert indexed labels back to original labels.
labelConverter = IndexToString(inputCol="prediction", outputCol="predictedLabel",
                               labels=labelIndexer.labels)
# Chain indexers and forest in a Pipeline
pipeline = Pipeline(stages=[labelIndexer, featureIndexer, rf, labelConverter])

"""**Training  of Random Forest**"""

# Train model.  This also runs the indexers.
model = pipeline.fit(trainingData)

"""**Prediction of random forest**"""

# Make predictions.
predictions = model.transform(validationData)

# Select example rows to display.
predictions.select("predictedLabel", "label", "features").show(5)

# Select (prediction, true label) and compute test error
evaluator = MulticlassClassificationEvaluator(
    labelCol="indexedLabel", predictionCol="prediction", metricName="accuracy")
accuracy = evaluator.evaluate(predictions)
print("Validation Error = %g" % (1.0 - accuracy))

rfModel = model.stages[2]
print(rfModel)  # summary only

"""**Evaluate the performance of Random Forest**"""

f1_score_evaluator = MulticlassClassificationEvaluator(labelCol="indexedLabel", predictionCol="prediction",metricName='f1')
f1_score = f1_score_evaluator.evaluate(predictions)
print("F1 score = %g" % (f1_score))