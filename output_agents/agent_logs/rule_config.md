# Recommender rule calibration analyst

## Prompt

You are the agent: Recommender rule calibration analyst.
Goal: Design transparent weights for popularity, personalized and sustainable POI recommenders.
Follow the task exactly. Be concise. Do not invent explanations outside the requested format.

Task:
Given the following POI statistics, return recommender weights for three strategies.
The sustainable strategy must reduce crowding and central hotspot pressure without ignoring tourist interests.
Weights inside popularity, personalized, sustainable.social and sustainable.personal should each be easy to interpret and roughly sum to 1.
Return only valid JSON using this schema:
{"popularity": {"popularity": 0.8, "budget": 0.1, "distance": 0.06, "culture": 0.04}, "personalized": {"interest": 0.55, "popularity": 0.16, "budget": 0.12, "distance": 0.08, "crowd_base": 0.05, "crowd_user": 0.12, "outdoor": 0.04, "culture": 0.03}, "sustainable": {"social": {"crowd": 0.3, "neighbourhood_relief": 0.25, "sustainable_value": 0.2, "local_economy": 0.15, "distance": 0.1}, "personal": {"interest": 0.48, "budget": 0.15, "distance": 0.16, "outdoor": 0.1, "popularity": 0.06, "culture": 0.05}, "alpha_base": 0.42, "alpha_user": 0.28, "diversity_rule": true}, "metadata": {"agent_reason": "string"}}

POI statistics:
{"n_pois": 57, "avg_popularity": 0.75, "central_share_top10": 1.0, "top10": [{"poi_name": "Barcelona Cathedral", "neighbourhood": "Gotic", "lat": 41.3862, "lon": 2.1799, "categories": "architecture,museum,religious", "popularity": 0.95, "capacity": 1000, "cost": 10.0, "outdoor": 0.4, "culture": 0.8, "local_economy": 0.7, "green": 0.6}, {"poi_name": "Barceloneta Beach", "neighbourhood": "La Barceloneta", "lat": 41.3897, "lon": 2.1765, "categories": "beach,viewpoint", "popularity": 0.9, "capacity": 1000, "cost": 0.0, "outdoor": 0.9, "culture": 0.4, "local_economy": 0.8, "green": 0.75}, {"poi_name": "Mercat dels Encants", "neighbourhood": "Dreta Eixample", "lat": 41.3875, "lon": 2.1806, "categories": "market,local", "popularity": 0.9, "capacity": 700, "cost": 0.0, "outdoor": 0.75, "culture": 0.0, "local_economy": 1.0, "green": 0.0}, {"poi_name": "Sant Antoni Market", "neighbourhood": "Dreta Eixample", "lat": 41.3875, "lon": 2.1806, "categories": "market,local", "popularity": 0.9, "capacity": 700, "cost": 0.0, "outdoor": 0.75, "culture": 0.0, "local_economy": 1.0, "green": 0.0}, {"poi_name": "Palau Macaya", "neighbourhood": "Dreta Eixample", "lat": 41.3875, "lon": 2.1806, "categories": "architecture,local", "popularity": 0.9, "capacity": 700, "cost": 0.0, "outdoor": 0.75, "culture": 0.65, "local_economy": 1.0, "green": 0.0}, {"poi_name": "Mercat de Gr\u00e0cia", "neighbourhood": "Dreta Eixample", "lat": 41.3875, "lon": 2.1806, "categories": "market,local", "popularity": 0.9, "capacity": 700, "cost": 0.0, "outdoor": 0.75, "culture": 0.0, "local_economy": 1.0, "green": 0.0}, {"poi_name": "Casa Batllo", "neighbourhood": "Dreta Eixample", "lat": 41.3862, "lon": 2.1795, "categories": "architecture,local", "popularity": 0.85, "capacity": 300, "cost": 10.0, "outdoor": 0.75, "culture": 0.65, "local_economy": 0.9, "green": 0.0}, {"poi_name": "La Pedrera", "neighbourhood": "Dreta Eixample", "lat": 41.3872, "lon": 2.1806, "categories": "architecture,local", "popularity": 0.85, "capacity": 300, "cost": 10.0, "outdoor": 0.75, "culture": 0.65, "local_economy": 0.9, "green": 0.0}, {"poi_name": "Casa Amatller", "neighbourhood": "Dreta Eixample", "lat": 41.3862, "lon": 2.1795, "categories": "architecture,local", "popularity": 0.85, "capacity": 300, "cost": 10.0, "outdoor": 0.75, "culture": 0.65, "local_economy": 0.9, "green": 0.0}, {"poi_name": "Joan Mir\u00f3 Park", "neighbourhood": "Dreta Eixample", "lat": 41.3862, "lon": 2.1795, "categories": "park,local", "popularity": 0.85, "capacity": 700, "cost": 0.0, "outdoor": 0.75, "culture": 0.0, "local_economy": 1.0, "green": 1.0}]}

## Answer

{
  "popularity": {"popularity": 0.8, "budget": 0.1, "distance": 0.06, "culture": 0.04},
  "personalized": {"interest": 0.55, "popularity": 0.16, "budget": 0.12, "distance": 0.08, "crowd_base": 0.05, "crowd_user": 0.12, "outdoor": 0.04, "culture": 0.03},
  "sustainable": {"social": {"crowd": 0.3, "neighbourhood_relief": 0.25, "sustainable_value": 0.2, "local_economy": 0.15, "distance": 0.1}, "personal": {"interest": 0.48, "budget": 0.15, "distance": 0.16, "outdoor": 0.1, "popularity": 0.06, "culture": 0.05}, "alpha_base": 0.42, "alpha_user": 0.28, "diversity_rule": true},
  "metadata": {"agent_reason": "The sustainable strategy reduces crowding and central hotspot pressure while considering tourist interests."}
}
