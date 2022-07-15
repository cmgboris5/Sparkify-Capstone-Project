# Data Scientist Capstone project
## Project Title: Sparkify

### Table of Contents
1. Project Introduction
2. Strategy
3. Metrics
4. EDA
5. Implementation
6. Refinement
7. Results
8. Conclusion


### Project Introduction:
Imagine you are working for music streaming company like Spotify or Pandora called Sparkify. Millions of users stream their favorite songs every day. Each user uses either the Free-tier with advertisement between the songs or the premium Subscription Plan. Users can upgrade, downgrade or cancel their service at any time. Hence, it’s crucial to make sure that users love the service provided by Sparkify. Every time a user interacts with the Sparkify app data is generated. Events such as playing a song, logging out, like a song etc. are all recorded. All this data contains key insights that can help the business thrive. The goal of this project is then to analyze this data and predict which group of users are expected to churn — either downgrading from premium to free or cancel their subscriptions altogether. In this post I am going to walk you through the steps I have taken to build the model using Spark


### Strategy

First we load the dataset and then clean the dataset after than we Perform EDA to get insights from data and get to know the distribution of data we define label and explore the dataset. After data preprocessing we do feature engineering and prepare the data using vector assembler and string indexer after that apply random forest on this dataset and evaluate the performance and then do hyper-parameter tuning of random forest and improve the performance

### Metrics
Since we are interested not only in precision (ensuring we identify as many users susceptible to churn as possible), but also in recall (ensuring the users we identify are actually likely to churn, since they’ll for example be proposed special offers), we propose to use F1-score to measure our machine learning classifier performance.

### EDA
Also perform EDA to get insights of the dataset and EDA also help us to get to know the distribution of the data acordinf to this result we get to know thw trend of the data


### Implementation
We split the user set into training (75%) and test (25%), and create a pipeline that assembles the features selected above, scales them, then runs a machine learning model; our problem is a classification one, so we used the following algorithms implemented in Spark:

Steps of implementation:

•	Split the full dataset into train, validation and test set.
•	Tune selected machine learning alogirthm using the validation dataset.
•	Score tuned machine learning model on the test dataset to verify it generalizes well


### Refinement
Let’s try to optimize our random forest model by adjusting its parameters: this is done by performing a grid search with different values of parameter such as  maxDepth , maxBins  and numTrees 

### Results
We have analyzed the sparkify dataset and come up with new features to predict churn. We then created a machine learning model and tuned it to improve its performance. We achieved an accuracy score of 60% and F1 score of 56% on the test dataset

### Conclusion

This capstone project is a great exercise allowing to put in practice several data science skills (data analysis, cleaning, feature extraction, machine learning pipeline creation, model evaluation and fine tuning…) to solve a problem close to those regularly encountered by customer-facing businesses.







  






