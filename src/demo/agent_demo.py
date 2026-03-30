from __future__ import annotations

import os
from typing import Any

from src.prompts.system_prompts import (
    SYSTEM_PROMPTS,
    build_purchase_history_summary,
    render_system_prompt_structured,
)
from src.analysis.knowledge_base import build_prompt_ready_knowledge_base


def local_mock_response(
    *,
    scenario_name: str,
    profile: dict[str, Any],
    knowledge_base: dict[str, dict[str, Any]],
) -> str:
    kb_items = list(knowledge_base.values())[:3]

    intro_map = {
        "young_digital_frequent": "Te comparto opciones muy alineadas con tu estilo de compra reciente.",
        "older_conservative_friction": "Quiero proponerte opciones claras y confiables, pensadas para una experiencia simple.",
        "vip_high_spend": "Preparé una selección curada con opciones relevantes para tu perfil de valor.",
    }

    lines = [intro_map.get(scenario_name, "Aquí tienes una selección personalizada para ti.")]

    for item in kb_items:
        lines.append(
            f"- producto: {item['product_id']} | categoría: {item['product_category']} | "
            f"razón: encaja con tu historial y destaca por su precio promedio de "
            f"${item['avg_real_price']:,.2f} y su buen desempeño comercial."
        )

    lines.append("Si alguna opción te interesa, puedo ayudarte a priorizar la más conveniente.")
    return "\n".join(lines)


def live_openai_response(
    *,
    scenario_name: str,
    profile: dict[str, Any],
    knowledge_base: dict[str, dict[str, Any]],
    client,
    model: str = "gpt-5.4-nano",
):
    prompt = render_system_prompt_structured(
        SYSTEM_PROMPTS[scenario_name],
        edad=profile["edad"],
        genero=profile["genero"],
        perfil_de_cliente=profile["perfil_de_cliente"],
        historial_compras=profile["historial_compras"],
        base_conocimiento=build_prompt_ready_knowledge_base(knowledge_base),
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": "Genera la recomendación personalizada final para este cliente."
            },
        ],
        max_output_tokens=220,
    )
    return response.output_text