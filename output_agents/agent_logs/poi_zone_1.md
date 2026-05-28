# Barcelona POI database curator

## Prompt

You are the agent: Barcelona POI database curator.
Goal: Create realistic structured POI records for a sustainable tourism recommender simulation.
Follow the task exactly. Be concise. Do not invent explanations outside the requested format.

Task:
Create exactly 10 distinct Barcelona POIs for this zone: Historic centre.
The neighbourhood value must be exactly one of these names, never a number: Gotic, El Raval, El Born, La Rambla, La Barceloneta, Sant Pere.
Useful real-place hints for this zone: Barcelona Cathedral, Santa Maria del Mar, Picasso Museum, Mercat de la Boqueria, Maritime Museum, History Museum of Catalonia, Ciutadella Park, Palau Guell, Barceloneta Beach, Born Cultural Centre.
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
      "n": "Barcelona Cathedral",
      "neighbourhood": "Gotic",
      "lat": 41.3862,
      "lon": 2.1799,
      "cats": "architecture,museum,religious",
      "pop": 0.95,
      "cap": 1000,
      "cost": 10,
      "outdoor": 0.4,
      "culture": 0.8,
      "local_economy": 0.7,
      "green": 0.6
    },
    {
      "n": "Mercat de la Boqueria",
      "neighbourhood": "La Barceloneta",
      "lat": 41.3925,
      "lon": 2.1828,
      "cats": "market,food",
      "pop": 0.75,
      "cap": 600,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.3
    },
    {
      "n": "Ciutadella Park",
      "neighbourhood": "El Born",
      "lat": 41.3867,
      "lon": 2.1953,
      "cats": "park,viewpoint",
      "pop": 0.8,
      "cap": 1000,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.6,
      "local_economy": 0.5,
      "green": 0.7
    },
    {
      "n": "Picasso Museum",
      "neighbourhood": "El Raval",
      "lat": 41.3829,
      "lon": 2.1694,
      "cats": "museum,art",
      "pop": 0.7,
      "cap": 500,
      "cost": 10,
      "outdoor": 0.3,
      "culture": 0.8,
      "local_economy": 0.4,
      "green": 0
    },
    {
      "n": "History Museum of Catalonia",
      "neighbourhood": "La Rambla",
      "lat": 41.3927,
      "lon": 2.1856,
      "cats": "museum,history",
      "pop": 0.6,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.3,
      "culture": 0.7,
      "local_economy": 0.2,
      "green": 0
    },
    {
      "n": "Palau Guell",
      "neighbourhood": "El Raval",
      "lat": 41.3856,
      "lon": 2.1799,
      "cats": "architecture,art",
      "pop": 0.8,
      "cap": 300,
      "cost": 15,
      "outdoor": 0.9,
      "culture": 0.6,
      "local_economy": 0.4,
      "green": 0
    },
    {
      "n": "Maritime Museum",
      "neighbourhood": "La Barceloneta",
      "lat": 41.3895,
      "lon": 2.1767,
      "cats": "museum,science",
      "pop": 0.7,
      "cap": 400,
      "cost": 10,
      "outdoor": 0.3,
      "culture": 0.5,
      "local_economy": 0.2,
      "green": 0
    },
    {
      "n": "Barceloneta Beach",
      "neighbourhood": "La Barceloneta",
      "lat": 41.3897,
      "lon": 2.1765,
      "cats": "beach,viewpoint",
      "pop": 0.9,
      "cap": 1000,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 0.8,
      "green": 0.5
    },
    {
      "n": "Born Cultural Centre",
      "neighbourhood": "El Born",
      "lat": 41.3869,
      "lon": 2.1937,
      "cats": "culture,local",
      "pop": 0.75,
      "cap": 500,
      "cost": 0,
      "outdoor": 0.5,
      "culture": 0.8,
      "local_economy": 1,
      "green": 0.6
    },
    {
      "n": "Sant Pere Church",
      "neighbourhood": "Gotic",
      "lat": 41.3872,
      "lon": 2.1951,
      "cats": "architecture,religious",
      "pop": 0.6,
      "cap": 200,
      "cost": 10,
      "outdoor": 0.3,
      "culture": 0.7,
      "local_economy": 0.4,
      "green": 0
    }
  ]
}
