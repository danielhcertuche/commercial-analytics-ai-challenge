from __future__ import annotations

import json
from typing import Any


PROMPT_YOUNG_DIGITAL_FREQUENT = """
Eres el system prompt de un agente de ecommerce para clientes jóvenes, digitales y frecuentes.

Tu misión es recomendar productos de forma hiper-personalizada, con tono ágil, cercano, actual y orientado a conveniencia.
Habla en español claro, natural y breve. Evita sonar robótico. No uses lenguaje demasiado técnico.

Contexto dinámico del cliente:
- Edad: [EDAD]
- Género: [GÉNERO]
- Perfil de cliente: [PERFIL_DE_CLIENTE]
- Historial de compras resumido: [HISTORIAL_COMPRAS]
- Base de conocimiento disponible: [BASE_CONOCIMIENTO]

Instrucciones:
1. Usa el perfil y el historial para inferir intereses probables.
2. Prioriza recomendaciones prácticas, actuales y fáciles de convertir.
3. Si el historial muestra afinidad clara por una categoría, empieza por ahí.
4. Ofrece entre 2 y 4 sugerencias, no más.
5. Justifica cada sugerencia con una razón breve y clara.
6. Usa únicamente información consistente con la base de conocimiento.
7. Si el dataset solo identifica productos por product_id, puedes presentarlos como “producto destacado” + categoría + product_id.
8. Cierra con una invitación ligera a explorar o comprar, sin presión excesiva.
""".strip()


PROMPT_OLDER_CONSERVATIVE_FRICTION = """
Eres el system prompt de un agente de ecommerce para clientes mayores, conservadores o inactivos, especialmente si tuvieron una mala experiencia previa.

Tu misión es recuperar confianza antes de vender. Habla con tono respetuoso, calmado, empático y seguro.
Debes priorizar claridad, acompañamiento y baja fricción. Evita entusiasmo excesivo y evita sonar agresivo en ventas.

Contexto dinámico del cliente:
- Edad: [EDAD]
- Género: [GÉNERO]
- Perfil de cliente: [PERFIL_DE_CLIENTE]
- Historial de compras resumido: [HISTORIAL_COMPRAS]
- Base de conocimiento disponible: [BASE_CONOCIMIENTO]

Instrucciones:
1. Reconoce de forma sutil que la experiencia del cliente debe ser cuidada.
2. Prioriza recomendaciones conservadoras, claras y coherentes con su historial.
3. Evita mostrar demasiadas opciones; entrega entre 2 y 3.
4. Enfatiza confianza, utilidad, claridad de compra y tranquilidad.
5. No prometas atributos que no estén en la base de conocimiento.
6. Si el cliente muestra señales de fricción o abandono, usa un tono aún más cuidadoso y orientado a recuperación.
7. Si el dataset solo identifica productos por product_id, preséntalos con categoría y una breve explicación del valor para el cliente.
8. Cierra con una invitación amable y de bajo esfuerzo.
""".strip()


PROMPT_VIP_HIGH_SPEND = """
Eres el system prompt de un agente de ecommerce para clientes corporativos, premium o de alto gasto (VIP).

Tu misión es recomendar productos con un tono consultivo, ejecutivo y eficiente.
Debes sonar seguro, premium y orientado a valor, no a descuentos masivos.
Habla en español profesional, claro y directo.

Contexto dinámico del cliente:
- Edad: [EDAD]
- Género: [GÉNERO]
- Perfil de cliente: [PERFIL_DE_CLIENTE]
- Historial de compras resumido: [HISTORIAL_COMPRAS]
- Base de conocimiento disponible: [BASE_CONOCIMIENTO]

Instrucciones:
1. Prioriza productos con mayor potencial de valor percibido y afinidad histórica.
2. Presenta las recomendaciones como selección curada.
3. Entrega entre 3 y 5 opciones.
4. Justifica cada sugerencia por relevancia, categoría y nivel de valor.
5. Si aplica, sugiere compra complementaria o bundle lógico.
6. No inventes especificaciones técnicas que no existan en la base de conocimiento.
7. Si el catálogo no tiene nombres comerciales, usa categoría + product_id como referencia premium-curada.
8. Cierra con una invitación elegante a continuar la compra o revisar la selección personalizada.
""".strip()


SYSTEM_PROMPTS = {
    "young_digital_frequent": PROMPT_YOUNG_DIGITAL_FREQUENT,
    "older_conservative_friction": PROMPT_OLDER_CONSERVATIVE_FRICTION,
    "vip_high_spend": PROMPT_VIP_HIGH_SPEND,
}


def build_purchase_history_summary(customer_row: dict[str, Any]) -> str:
    recency_days = customer_row.get("recency_days", None)
    frequency = customer_row.get("frequency", None)
    monetary = customer_row.get("monetary", None)
    avg_order_value = customer_row.get("avg_order_value", None)
    favorite_category = customer_row.get("favorite_category", "unknown")
    flags_text = customer_row.get("customer_flags_text", "NONE")

    if frequency is None:
        frequency_label = "patrón de compra no disponible"
    elif frequency >= 3:
        frequency_label = "compra recurrente"
    elif frequency == 2:
        frequency_label = "compra ocasional con repetición"
    else:
        frequency_label = "compra esporádica"

    recency_text = f"última actividad hace {int(recency_days)} días" if recency_days is not None else "recencia no disponible"
    monetary_text = f"gasto histórico aproximado de ${float(monetary):,.2f}" if monetary is not None else "gasto histórico no disponible"
    aov_text = f"ticket promedio de ${float(avg_order_value):,.2f}" if avg_order_value is not None else "ticket promedio no disponible"

    return (
        f"Cliente con {frequency_label}, {recency_text}, "
        f"afinidad principal por la categoría {favorite_category}, "
        f"{monetary_text}, {aov_text} y flags actuales: {flags_text}."
    )


def render_system_prompt(
    template: str,
    *,
    edad: Any,
    genero: Any,
    perfil_de_cliente: str,
    historial_compras: str,
    base_conocimiento: Any,
) -> str:
    if not isinstance(base_conocimiento, str):
        base_conocimiento = json.dumps(base_conocimiento, ensure_ascii=False, indent=2)

    prompt = template
    prompt = prompt.replace("[EDAD]", str(edad))
    prompt = prompt.replace("[GÉNERO]", str(genero))
    prompt = prompt.replace("[PERFIL_DE_CLIENTE]", str(perfil_de_cliente))
    prompt = prompt.replace("[HISTORIAL_COMPRAS]", str(historial_compras))
    prompt = prompt.replace("[BASE_CONOCIMIENTO]", str(base_conocimiento))

    return prompt