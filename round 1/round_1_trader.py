{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "eb1b28a6-2775-4782-8398-799c5bff04a8",
   "metadata": {},
   "outputs": [],
   "source": [
    "from datamodel import OrderDepth, UserId, TradingState, Order\n",
    "from typing import List\n",
    "import string\n",
    "\n",
    "class Trader:\n",
    "    '''\n",
    "    def run(self, state: TradingState):\n",
    "        print(\"traderData: \" + state.traderData)\n",
    "        print(\"Observations: \" + str(state.observations))\n",
    "\n",
    "\t\t# Orders to be placed on exchange matching engine\n",
    "        result = {}\n",
    "        for product in state.order_depths:\n",
    "            order_depth: OrderDepth = state.order_depths[product]\n",
    "            orders: List[Order] = []\n",
    "            acceptable_price = 10  # Participant should calculate this value\n",
    "            print(\"Acceptable price : \" + str(acceptable_price))\n",
    "            print(\"Buy Order depth : \" + str(len(order_depth.buy_orders)) + \", Sell order depth : \" + str(len(order_depth.sell_orders)))\n",
    "    \n",
    "            if len(order_depth.sell_orders) != 0:\n",
    "                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]\n",
    "                if int(best_ask) < acceptable_price:\n",
    "                    print(\"BUY\", str(-best_ask_amount) + \"x\", best_ask)\n",
    "                    orders.append(Order(product, best_ask, -best_ask_amount))\n",
    "    \n",
    "            if len(order_depth.buy_orders) != 0:\n",
    "                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]\n",
    "                if int(best_bid) > acceptable_price:\n",
    "                    print(\"SELL\", str(best_bid_amount) + \"x\", best_bid)\n",
    "                    orders.append(Order(product, best_bid, -best_bid_amount))\n",
    "            \n",
    "            result[product] = orders\n",
    "    \n",
    "\t\t    # String value holding Trader state data required. \n",
    "\t\t\t\t# It will be delivered as TradingState.traderData on next execution.\n",
    "        traderData = \"SAMPLE\" \n",
    "        \n",
    "\t\t\t\t# Sample conversion request. Check more details below. \n",
    "        conversions = 1\n",
    "        return result, conversions, traderData\n",
    "    '''\n",
    "    def run(self, state: TradingState):\n",
    "        print(\"traderData: \" + state.traderData)\n",
    "        print(\"Observations: \" + str(state.observations))\n",
    "\n",
    "\t\t# how many orders can I place on the rainforest resin?\n",
    "        # if I place a lot of bids and a lot of asks, do they get cancelled out?\n",
    "        result = {}\n",
    "        orders: List[Order] = []\n",
    "        \n",
    "        result['RAINFOREST_RESIN'] = [Order('RAINFOREST_RESIN', 9998, 1000), Order('RAINFOREST_RESIN', 10002, -1000)]\n",
    "        traderData = \"\"\n",
    "        conversions = 0\n",
    "        return result, conversions, traderData"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.11"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
