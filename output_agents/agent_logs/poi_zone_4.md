# Barcelona POI database curator

## Prompt

You are the agent: Barcelona POI database curator.
Goal: Create realistic structured POI records for a sustainable tourism recommender simulation.
Follow the task exactly. Be concise. Do not invent explanations outside the requested format.

Task:
Create exactly 10 distinct Barcelona POIs for this zone: Gracia and northern viewpoints.
The neighbourhood value must be exactly one of these names, never a number: Vila de Gracia, La Salut, El Carmel, Horta, Tibidabo, Guinardo.
Useful real-place hints for this zone: Park Guell, Casa Vicens, Bunkers del Carmel, Temple del Tibidabo, Tibidabo Park, Labyrinth Park of Horta, Gracia squares, Guinardo Park, Mercat de la Llibertat, Fabra Observatory.
POI names should be actual attractions, parks, museums, markets, streets, churches or viewpoints, not generic numbered items.
Do not repeat any POI name inside the answer. Do not put Sagrada Familia or Casa Batllo outside the Eixample/Sagrada Familia zone.
Use only these category tags, comma separated: architecture, religious, museum, park, market, food, beach, viewpoint, shopping, nightlife, family, science, local.
Use plausible Barcelona coordinates. Numeric scores must be between 0 and 1, except capacity and cost.
Popularity should reflect expected tourist fame, not personal preference. Include famous and less famous places.
Use varied numeric values. Do not copy the same scores for every POI.
Outdoor guidance: parks, beaches, viewpoints and streets should have outdoor above 0.75; indoor museums and churches below 0.35.
Cost guidance: streets, parks, beaches and markets can be 0; museums usually 6-20; iconic paid monuments 15-35.
Capacity guidance: small museums/churches 150-450; big parks/beaches/streets 700-1500; markets/monuments 300-900.
Use the compact keys from the schema to keep the answer short.
Return only valid JSON with this schema:
{"pois": [{"n": "POI name", "neighbourhood": "one allowed neighbourhood", "lat": "float", "lon": "float", "cats": "comma tags", "pop": "0-1", "cap": "integer", "cost": "euros", "outdoor": "0-1", "culture": "0-1", "local_economy": "0-1", "green": "0-1"}]}

## Answer

{
  "pois": [
    {
      "n": "Park Güell",
      "neighbourhood": "Vila de Gracia",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "architecture,park,museum,local",
      "pop": 0.85,
      "cap": 700,
      "cost": 15,
      "outdoor": 0.9,
      "culture": 0.6,
      "local_economy": 0.4,
      "green": 0.9
    },
    {
      "n": "Casa Vicens",
      "neighbourhood": "Vila de Gracia",
      "lat": 41.3872,
      "lon": 2.1806,
      "cats": "architecture,museum,local",
      "pop": 0.8,
      "cap": 500,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.7,
      "local_economy": 0.6,
      "green": 0.8
    },
    {
      "n": "Temple del Tibidabo",
      "neighbourhood": "Horta",
      "lat": 41.3925,
      "lon": 2.1795,
      "cats": "religion,viewpoint,museum",
      "pop": 0.75,
      "cap": 600,
      "cost": 18,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 0.3,
      "green": 0.2
    },
    {
      "n": "Bunkers del Carmel",
      "neighbourhood": "El Carmel",
      "lat": 41.3957,
      "lon": 2.1863,
      "cats": "architecture,viewpoint,military",
      "pop": 0.7,
      "cap": 400,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.5,
      "local_economy": 0.2,
      "green": 0.1
    },
    {
      "n": "Mercat de la Llibertat",
      "neighbourhood": "Vila de Gracia",
      "lat": 41.3867,
      "lon": 2.1795,
      "cats": "market,local",
      "pop": 0.7,
      "cap": 500,
      "cost": 0,
      "outdoor": 0.8,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.2
    },
    {
      "n": "Labyrinth Park of Horta",
      "neighbourhood": "Horta",
      "lat": 41.3915,
      "lon": 2.1786,
      "cats": "park,local",
      "pop": 0.65,
      "cap": 400,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.8
    },
    {
      "n": "Gracia squares",
      "neighbourhood": "Vila de Gracia",
      "lat": 41.3865,
      "lon": 2.1793,
      "cats": "viewpoint,local",
      "pop": 0.7,
      "cap": 300,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.5
    },
    {
      "n": "Guinardo Park",
      "neighbourhood": "Guinardo",
      "lat": 41.3872,
      "lon": 2.1806,
      "cats": "park,local",
      "pop": 0.5,
      "cap": 300,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.8
    },
    {
      "n": "Fabra Observatory",
      "neighbourhood": "El Carmel",
      "lat": 41.3957,
      "lon": 2.1863,
      "cats": "science,local",
      "pop": 0.4,
      "cap": 200,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.5,
      "local_economy": 1,
      "green": 0.7
    },
    {
      "n": "Bunkers del Carmel",
      "neighbourhood": "El Carmel",
      "lat": 41.3957,
      "lon": 2.1863,
      "cats": "architecture,viewpoint,military",
      "pop": 0.7,
      "cap": 400,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.5,
      "local_economy": 1,
      "green": 0.1
    }
  ]
}
