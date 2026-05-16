import json
import os
from typing import Optional

from google import genai
from google.genai import types

from agent.tools.calorie_calc import calculate_calories
from agent.tools.waypoint_gen import generate_ellipse_waypoints, scale_waypoints
from agent.tools.route_compute import compute_route
from models.response import RouteResponse, Waypoint


TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="generate_waypoints",
        description="Generate circular waypoints around a starting point for a running loop.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "lat": types.Schema(type=types.Type.NUMBER, description="Center latitude"),
                "lon": types.Schema(type=types.Type.NUMBER, description="Center longitude"),
                "target_km": types.Schema(type=types.Type.NUMBER, description="Desired total loop distance in km"),
                "num_points": types.Schema(type=types.Type.INTEGER, description="Number of waypoints 3-6"),
                "bearing_offset_deg": types.Schema(type=types.Type.NUMBER, description="Rotate ellipse 0-360"),
            },
            required=["lat", "lon", "target_km"],
        ),
    ),
    types.FunctionDeclaration(
        name="compute_route",
        description="Call OSRM to get the actual walking route through waypoints, looping back to start.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "start_lat": types.Schema(type=types.Type.NUMBER),
                "start_lon": types.Schema(type=types.Type.NUMBER),
                "waypoints_json": types.Schema(
                    type=types.Type.STRING,
                    description='Waypoints as JSON string: \'[{"lat":13.7,"lon":100.5},...]\'',
                ),
            },
            required=["start_lat", "start_lon", "waypoints_json"],
        ),
    ),
    types.FunctionDeclaration(
        name="adjust_waypoints",
        description="Scale waypoints outward (>1) or inward (<1) to adjust route distance.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "waypoints_json": types.Schema(type=types.Type.STRING, description="Current waypoints as JSON string"),
                "center_lat": types.Schema(type=types.Type.NUMBER),
                "center_lon": types.Schema(type=types.Type.NUMBER),
                "scale_factor": types.Schema(type=types.Type.NUMBER, description="e.g. 1.2 to expand, 0.9 to shrink"),
            },
            required=["waypoints_json", "center_lat", "center_lon", "scale_factor"],
        ),
    ),
    types.FunctionDeclaration(
        name="calculate_calories",
        description="Calculate calories burned for a running distance.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "distance_km": types.Schema(type=types.Type.NUMBER),
                "weight_kg": types.Schema(type=types.Type.NUMBER),
                "pace_min_per_km": types.Schema(type=types.Type.NUMBER),
            },
            required=["distance_km", "weight_kg", "pace_min_per_km"],
        ),
    ),
    types.FunctionDeclaration(
        name="finalize_route",
        description="Call when satisfied. Provide final waypoints, geometry, stats, and Thai summary.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "waypoints_json": types.Schema(type=types.Type.STRING, description='Final waypoints JSON: \'[{"lat":...,"lon":...}]\''),
                "geometry_json": types.Schema(type=types.Type.STRING, description="Geometry from compute_route as JSON string"),
                "total_km": types.Schema(type=types.Type.NUMBER),
                "estimated_calories": types.Schema(type=types.Type.NUMBER),
                "estimated_minutes": types.Schema(type=types.Type.INTEGER),
                "agent_summary": types.Schema(type=types.Type.STRING, description="2-3 sentences in Thai about the route"),
            },
            required=["waypoints_json", "geometry_json", "total_km", "estimated_calories", "estimated_minutes", "agent_summary"],
        ),
    ),
])

SYSTEM_PROMPT = """You are a Bangkok running route planner AI. Create safe circular running routes.

Rules:
- Route MUST return to starting point (circular loop)
- Target distance tolerance: ±10%
- Use 4 waypoints for routes under 10 km, 5-6 for longer
- Try bearing_offset_deg=45 or 90 if first attempt is off target
- Max 6 tool calls total — be efficient
- Write agent_summary in Thai (2-3 sentences about the route character)
- waypoints_json and geometry_json must be valid JSON strings

Workflow: generate_waypoints → compute_route → check distance → adjust if needed → calculate_calories → finalize_route"""


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "generate_waypoints":
        wps = generate_ellipse_waypoints(
            lat=tool_input["lat"],
            lon=tool_input["lon"],
            target_km=tool_input["target_km"],
            num_points=int(tool_input.get("num_points", 4)),
            bearing_offset_deg=float(tool_input.get("bearing_offset_deg", 0.0)),
        )
        return json.dumps({"waypoints_json": json.dumps(wps)})

    elif tool_name == "compute_route":
        waypoints = json.loads(tool_input["waypoints_json"])
        result = compute_route(
            start_lat=tool_input["start_lat"],
            start_lon=tool_input["start_lon"],
            waypoints=waypoints,
        )
        result["geometry_json"] = json.dumps(result.pop("geometry"))
        return json.dumps(result)

    elif tool_name == "adjust_waypoints":
        waypoints = json.loads(tool_input["waypoints_json"])
        scaled = scale_waypoints(
            waypoints=waypoints,
            center_lat=tool_input["center_lat"],
            center_lon=tool_input["center_lon"],
            scale_factor=tool_input["scale_factor"],
        )
        return json.dumps({"waypoints_json": json.dumps(scaled)})

    elif tool_name == "calculate_calories":
        cal = calculate_calories(
            distance_km=tool_input["distance_km"],
            weight_kg=tool_input["weight_kg"],
            pace_min_per_km=tool_input["pace_min_per_km"],
        )
        return json.dumps({"calories": cal})

    elif tool_name == "finalize_route":
        return json.dumps({"status": "finalized"})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def plan_route(lat, lon, target_km, weight_kg, pace_min_per_km) -> RouteResponse:
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[TOOLS],
    )

    user_message = (
        f"Plan a circular running route starting at lat={lat}, lon={lon}. "
        f"Target distance: {target_km} km. "
        f"Runner weight: {weight_kg} kg, pace: {pace_min_per_km} min/km. "
        f"Generate waypoints, compute the route, adjust if needed, calculate calories, then finalize."
    )

    chat = client.chats.create(model="gemini-2.5-flash", config=config)
    response = chat.send_message(user_message)
    final_tool_input: Optional[dict] = None

    for _ in range(10):
        fn_calls = [
            p.function_call
            for p in response.candidates[0].content.parts
            if p.function_call
        ]
        if not fn_calls:
            break

        tool_results = []
        for fc in fn_calls:
            tool_input = dict(fc.args)
            if fc.name == "finalize_route":
                final_tool_input = tool_input

            result_str = _execute_tool(fc.name, tool_input)
            tool_results.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response={"result": result_str},
                    )
                )
            )

        if final_tool_input is not None:
            break

        response = chat.send_message(tool_results)

    if final_tool_input is None:
        raise RuntimeError("Agent did not finalize a route. Please try again.")

    waypoints = json.loads(final_tool_input["waypoints_json"])
    geometry = json.loads(final_tool_input["geometry_json"])

    return RouteResponse(
        waypoints=[Waypoint(lat=w["lat"], lon=w["lon"]) for w in waypoints],
        geometry=geometry,
        total_km=final_tool_input["total_km"],
        estimated_calories=final_tool_input["estimated_calories"],
        estimated_minutes=int(final_tool_input["estimated_minutes"]),
        agent_summary=final_tool_input["agent_summary"],
    )
