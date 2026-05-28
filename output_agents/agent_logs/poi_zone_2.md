# Barcelona POI database curator

## Prompt

You are the agent: Barcelona POI database curator.
Goal: Create realistic structured POI records for a sustainable tourism recommender simulation.
Follow the task exactly. Be concise. Do not invent explanations outside the requested format.

Task:
Create exactly 10 distinct Barcelona POIs for this zone: Eixample and Sagrada Familia.
The neighbourhood value must be exactly one of these names, never a number: Dreta Eixample, Esquerra Eixample, Sagrada Familia, Sant Antoni, Fort Pienc, Nova Esquerra Eixample.
Useful real-place hints for this zone: Sagrada Familia, Casa Batllo, La Pedrera, Casa Amatller, Sant Antoni Market, Mercat dels Encants, Design Museum, Palau Macaya, Egyptian Museum, Joan Miro Park.
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
      "n": "Casa Batllo",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "architecture,local",
      "pop": 0.85,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.75,
      "culture": 0.6,
      "local_economy": 0.9,
      "green": 0
    },
    {
      "n": "La Pedrera",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3872,
      "lon": 2.1806,
      "cats": "architecture,local",
      "pop": 0.85,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.75,
      "culture": 0.6,
      "local_economy": 0.9,
      "green": 0
    },
    {
      "n": "Mercat dels Encants",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3875,
      "lon": 2.1806,
      "cats": "market,local",
      "pop": 0.9,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.75,
      "culture": 0,
      "local_economy": 1,
      "green": 0
    },
    {
      "n": "Casa Amatller",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "architecture,local",
      "pop": 0.85,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.75,
      "culture": 0.6,
      "local_economy": 0.9,
      "green": 0
    },
    {
      "n": "Sant Antoni Market",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3875,
      "lon": 2.1806,
      "cats": "market,local",
      "pop": 0.9,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.75,
      "culture": 0,
      "local_economy": 1,
      "green": 0
    },
    {
      "n": "Joan Miró Park",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "park,local",
      "pop": 0.85,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.75,
      "culture": 0,
      "local_economy": 1,
      "green": 1
    },
    {
      "n": "Casa Vicens",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "architecture,local",
      "pop": 0.85,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.75,
      "culture": 0.6,
      "local_economy": 0.9,
      "green": 0
    },
    {
      "n": "Palau Macaya",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3875,
      "lon": 2.1806,
      "cats": "architecture,local",
      "pop": 0.9,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.75,
      "culture": 0,
      "local_economy": 1,
      "green": 0
    },
    {
      "n": "Egyptian Museum",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "museum,local",
      "pop": 0.85,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.35,
      "culture": 0.6,
      "local_economy": 0.9,
      "green": 0
    },
    {
      "n": "Mercat de Gràcia",
      "neighbourhood": "Dreta Eixample",
      "lat": 41.3875,
      "lon": 2.1806,
      "cats": "market,local",
      "pop": 0.9,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.75,
      "culture": 0,
      "local_economy": 1,
      "green": 0
    }
  ]
}
