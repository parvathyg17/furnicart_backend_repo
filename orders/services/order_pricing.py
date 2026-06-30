# from decimal import Decimal


# def sum_order_line_offer_discount(
#     order,
# ):

#     total = Decimal(
#         "0.00",
#     )

#     for line in order.lines.all():

#         amount = (
#             line.discount_amount
#             or Decimal(
#                 "0.00",
#             )
#         )

#         total += amount

#     return total.quantize(
#         Decimal(
#             "0.01",
#         ),
#     )


# def order_subtotal_gross(
#     order,
# ):

#     return (
#         order.subtotal
#         + sum_order_line_offer_discount(
#             order,
#         )
#     ).quantize(
#         Decimal(
#             "0.01",
#         ),
#     )
