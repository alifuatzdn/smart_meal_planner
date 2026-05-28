import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from pathlib import Path

# Define relative paths based on script location
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
REPORTS_DIR = BASE_DIR / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

processed_train_path = DATA_DIR / 'processed_X_train.csv'
recipes_path = DATA_DIR / 'recipes_processed.csv'
clustered_data_path = DATA_DIR / 'clustered_data.csv'

# 1. Read previously saved data
try:
    X_train = pd.read_csv(processed_train_path)
    df = pd.read_csv(recipes_path)
except FileNotFoundError:
    print(f"Error: Could not find dataset. Please run src/features/preprocessing.py first!")
    exit()

# 2. Find optimal K using Elbow Method and Silhouette Score
print("Calculating Elbow Method and Silhouette Scores to find optimal K...")
wcss = []
silhouette_scores = {}
K_range = range(2, 30)
for k in K_range:
    kmeans_temp = KMeans(n_clusters=k, random_state=42, n_init='auto')
    labels = kmeans_temp.fit_predict(X_train)
    wcss.append(kmeans_temp.inertia_)
    silhouette_scores[k] = silhouette_score(X_train, labels)

plt.figure(figsize=(10, 6))
plt.plot(K_range, wcss, marker='o', linestyle='--')
plt.title('Elbow Method For Optimal k')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Within-Cluster Sum of Square (WCSS)')
plt.grid(True)
plt.savefig(REPORTS_DIR / 'elbow_plot.png')
print(f"Elbow plot saved to {REPORTS_DIR / 'elbow_plot.png'}")
plt.close()

# Automatically select the best 'k' based on the highest Silhouette Score
k = max(silhouette_scores, key=silhouette_scores.get)
print(f"Automatically found optimal k={k} (Highest Silhouette Score: {silhouette_scores[k]:.4f})")

print(f"Training K-Means Model with k={k}...")
kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
kmeans.fit(X_train)

# 3. Add results to the original dataset
df['cluster_id'] = kmeans.labels_

print("--- Clustering Results ---")
print(df[['recipe_name', 'cluster_id']].head())

# --- VISUALIZATION (PCA to 2D) ---

print("Creating 2D plot of clusters...")
pca = PCA(n_components=2)
data_2d = pca.fit_transform(X_train)

df_plot = pd.DataFrame(data_2d, columns=['Component_1', 'Component_2'])
df_plot['Cluster'] = df['cluster_id']

plt.figure(figsize=(12, 8))
sns.scatterplot(x='Component_1', y='Component_2', hue='Cluster', data=df_plot, palette='tab20', alpha=0.7)
plt.title('2D Dimension Reduction (PCA) of Recipe Clusters')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(REPORTS_DIR / 'pca_clusters_plot.png')
print(f"PCA plot saved to {REPORTS_DIR / 'pca_clusters_plot.png'}")
plt.close()


# 4. Save Clustered Data for Scoring
df.to_csv(clustered_data_path, index=False)
print(f"\nclustering.py completed. Clustered data saved as '{clustered_data_path}'.")
