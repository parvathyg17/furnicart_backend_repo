from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _money_str(
    value,
):

    n = Decimal(
        str(
            value,
        ),
    ).quantize(
        Decimal(
            "0.01",
        ),
    )

    return f"INR {n:,.2f}"


def build_order_invoice_pdf(
    order,
):

    """
    Build a PDF invoice (bytes) for a persisted ``Order`` instance.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Invoice {order.order_number}",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="InvTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
        textColor=colors.HexColor("#2c241c"),
    )

    normal = ParagraphStyle(
        name="InvNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#3d3830"),
    )

    muted = ParagraphStyle(
        name="InvMuted",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6b635c"),
    )

    story = []

    story.append(
        Paragraph(
            "FURNICART",
            title_style,
        ),
    )

    story.append(
        Paragraph(
            "Tax invoice / Order summary",
            muted,
        ),
    )

    story.append(
        Spacer(
            1,
            0.6 * cm,
        ),
    )

    placed = timezone.localtime(
        order.placed_at,
    ).strftime(
        "%d %b %Y, %H:%M",
    )

    meta_rows = [
        [
            "Order ID",
            order.order_number,
        ],
        [
            "Date",
            placed,
        ],
        [
            "Status",
            order.get_status_display(),
        ],
        [
            "Payment",
            order.get_payment_method_display(),
        ],
    ]

    meta_table = Table(
        meta_rows,
        colWidths=[
            3.2 * cm,
            12 * cm,
        ],
    )

    meta_table.setStyle(
        TableStyle(
            [
                (
                    "FONT",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "Helvetica",
                    9,
                ),
                (
                    "TEXTCOLOR",
                    (
                        0,
                        0,
                    ),
                    (
                        0,
                        -1,
                    ),
                    colors.HexColor("#6b635c"),
                ),
                (
                    "TEXTCOLOR",
                    (
                        1,
                        0,
                    ),
                    (
                        1,
                        -1,
                    ),
                    colors.HexColor("#2c241c"),
                ),
                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),
                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    4,
                ),
            ],
        ),
    )

    story.append(
        meta_table,
    )

    story.append(
        Spacer(
            1,
            0.5 * cm,
        ),
    )

    story.append(
        Paragraph(
            "<b>Ship to</b>",
            normal,
        ),
    )

    ship_lines = [
        f"{order.shipping_name} · {order.shipping_phone}",
        ", ".join(
            filter(
                bool,
                [
                    order.shipping_address_line,
                    order.shipping_city,
                    f"{order.shipping_state} {order.shipping_pincode}",
                ],
            ),
        ),
    ]

    for line in ship_lines:

        story.append(
            Paragraph(
                escape(
                    line,
                ),
                normal,
            ),
        )

    story.append(
        Spacer(
            1,
            0.6 * cm,
        ),
    )

    table_data = [
        [
            "Item",
            "SKU",
            "Qty",
            "Unit",
            "Line total",
        ],
    ]

    for line in order.lines.all():

        name = f"{line.product_name} ({line.variant_name})"

        table_data.append(
            [
                name[:72],
                line.sku[:24],
                str(
                    line.quantity,
                ),
                _money_str(
                    line.unit_price,
                ),
                _money_str(
                    line.line_total,
                ),
            ],
        )

    items_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            7.2 * cm,
            2.6 * cm,
            1.2 * cm,
            2.2 * cm,
            2.4 * cm,
        ],
    )

    items_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    colors.HexColor("#efe8df"),
                ),
                (
                    "FONT",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    "Helvetica-Bold",
                    8,
                ),
                (
                    "FONT",
                    (
                        0,
                        1,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "Helvetica",
                    8,
                ),
                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.25,
                    colors.HexColor("#d4c9bc"),
                ),
                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),
                (
                    "ALIGN",
                    (
                        2,
                        1,
                    ),
                    (
                        2,
                        -1,
                    ),
                    "CENTER",
                ),
                (
                    "ALIGN",
                    (
                        3,
                        1,
                    ),
                    (
                        4,
                        -1,
                    ),
                    "RIGHT",
                ),
                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    4,
                ),
                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3,
                ),
            ],
        ),
    )

    story.append(
        items_table,
    )

    story.append(
        Spacer(
            1,
            0.5 * cm,
        ),
    )

    totals = [
        [
            "Subtotal",
            _money_str(
                order.subtotal,
            ),
        ],
        [
            "Tax (GST)",
            _money_str(
                order.tax_total,
            ),
        ],
        [
            "Shipping",
            _money_str(
                order.shipping_total,
            ),
        ],
        [
            "Discounts",
            _money_str(
                order.discount_total,
            ),
        ],
        [
            "Grand total",
            _money_str(
                order.grand_total,
            ),
        ],
    ]

    totals_table = Table(
        totals,
        colWidths=[
            4.5 * cm,
            4.5 * cm,
        ],
        hAlign="RIGHT",
    )

    totals_table.setStyle(
        TableStyle(
            [
                (
                    "FONT",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -2,
                    ),
                    "Helvetica",
                    9,
                ),
                (
                    "FONT",
                    (
                        0,
                        -1,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "Helvetica-Bold",
                    10,
                ),
                (
                    "ALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "RIGHT",
                ),
                (
                    "LINEABOVE",
                    (
                        0,
                        -1,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.5,
                    colors.HexColor("#2c241c"),
                ),
                (
                    "TOPPADDING",
                    (
                        0,
                        -1,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    6,
                ),
            ],
        ),
    )

    story.append(
        totals_table,
    )

    story.append(
        Spacer(
            1,
            0.8 * cm,
        ),
    )

    story.append(
        Paragraph(
            "This is a computer-generated document and does not require a signature.",
            muted,
        ),
    )

    doc.build(
        story,
    )

    pdf_bytes = buffer.getvalue()

    buffer.close()

    return pdf_bytes
