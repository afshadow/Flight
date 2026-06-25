{
    "codex_agent_system": {
        "version": "2.1.0",
        "environment": "Production_UAV_Routing",
        "timestamp_utc": "2026-06-24T13:17:00Z"
    },
    "agents": [
        {
            "agent_id": "route_planner_agent",
            "role": "Навигационный ИИ-архитектор БПЛА",
            "goal": "Анализировать склеенные массивы растров высот и строить оптимальный 3D-маршрут А* с минимальным расходом энергии и обходом препятствий.",
            "backstory": "Эксперт в области геоинформационных систем (ГИС) и трехмерной авиационной навигации. Способен обрабатывать пиксельные матрицы рельефа и преобразовывать их в безопасные эшелоны полета.",
            "llm_config": {
                "model": "gpt-4o",
                "temperature": 0.2,
                "max_tokens": 1500
            },
            "allowed_tools": [
                "raster_processor.load_and_stitch_rasters",
                "router.calculate_route"
            ],
            "constraints": {
                "min_safe_altitude_m": 120.0,
                "max_climb_angle_deg": 15.0,
                "forbidden_zones_grid_chips": []
            }
        },
        {
            "agent_id": "mission_validator_agent",
            "role": "Инспектор безопасности полетов",
            "goal": "Проверять сгенерированный агентом 'route_planner_agent' массив точек на строгое соответствие физическим ограничениям самолета и высотам рельефа.",
            "backstory": "Автоматизированный аудитор систем управления движением. Блокирует любые маршруты, где абсолютная высота полета (altitude_amsl) опускается ниже безопасного буфера над точкой рельефа (terrain_elevation).",
            "llm_config": {
                "model": "gpt-4-turbo",
                "temperature": 0.0
            },
            "allowed_tools": [
                "agent_exporter.validate_json_schema"
            ],
            "dependencies": [
                "route_planner_agent"
            ]
        }
    ],
    "agent_execution_pipeline": {
        "input_data": {
            "source_rasters": [
                "kyiv-route-google-squares/01_O-12.png",
                "kyiv-route-google-squares/02_P-12.png"
            ],
            "grid_layout": [
                [
                    "kyiv-route-google-squares/01_O-12.png",
                    "kyiv-route-google-squares/02_P-12.png"
                ]
            ],
            "start_coordinates": [160, 640],
            "end_coordinates": [2400, 640]
        },
        "output_format": {
            "target_file": "agent_task.json",
            "schema": "Mavlink_Compliant_V2"
        }
    }
}
