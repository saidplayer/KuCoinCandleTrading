import sys, json, requests, time, os, pandas
from datetime import timezone, datetime
import tkinter as tk
from tkinter import *
from tkinter import scrolledtext, ttk
from tkinterweb import HtmlFrame
import threading
import plotly.express as px
import plotly.graph_objects as go
sys.path.insert(0,"include")
from include.get_candle import get_candle
from include.get_tick import get_tick
from include.db import db_insert, db_read, db_update, db_update_field, db_get_field
from include.send_order import send_limit_order, send_stoplimit_order, send_market_order
from include.cancel_order import cancel_order, cancel_all_orders
from include.get_orders import get_pending_orders, get_triggered_orders, get_all_orders, get_positions
from include.get_account import get_account
from include.close_order import close_order
from include.get_fills import get_report


def log_prnt(a):
    bb.insert(END, str(a) + "\n")
    bb.see(tk.END)

def order_prnt(a):
    aa.insert(END, str(a) + "\n")
    aa.see(tk.END)

def read_settings():
    # return
    global symbol, pair, candle_size_min, candle_size_max, leverage, order_size_scale, exposure,order_level_scale, order_bigSL
    global order_profit_scale, order_cancellation, order_expiration, order_side, order_level, order_TP, order_SL, orphan_limit
    global trail_profit, trail_SL, trade_periods_h, trade_periods_m, trade_periods, time_offset, step_time, time_frame, second_sl
    with open("settings.json") as settings_file:
        data = json.load(settings_file)
        symbol              = data["symbol"]
        pair                = data["pair"]
        candle_size_min     = data["candle_size_min"]
        candle_size_max     = data["candle_size_max"]
        leverage            = data["leverage"]
        order_size_scale    = data["order_size_scale"]
        exposure            = data["exposure"]
        order_level_scale   = data["order_level_scale"]
        loss_profit_scale   = data["loss_profit_scale"]
        order_cancellation  = data["order_cancellation"]
        order_expiration    = data["order_expiration"]
        order_side          = data["order_side"]
        order_level         = data["order_level"]
        order_TP            = data["order_TP"]
        order_SL            = data["order_SL"]
        trail_profit        = data["trail_profit"]
        trail_SL            = data["trail_SL"]
        order_bigSL         = data["order_bigSL"]
        second_sl           = data["second_sl"]
        manual_sl           = data["manual_sl"]
        trade_periods_h     = data["trade_periods_h"]
        trade_periods_m     = data["trade_periods_m"]
        trade_periods       = data["trade_periods"]
        pending_tolerance   = data["pending_tolerance"]
        stop_tolerance      = data["stop_tolerance"]
        time_offset         = data["time_offset"]
        step_time           = data["step_time"]
        time_frame          = data["time_frame"]
        orphan_limit        = data["orphan_limit"]
    settings_file.close()


with open("settings.json") as settings_file:
    data = json.load(settings_file)
    symbol              = data["symbol"]
    pair                = data["pair"]
    candle_size_min     = data["candle_size_min"]
    candle_size_max     = data["candle_size_max"]
    leverage            = data["leverage"]
    order_size_scale    = data["order_size_scale"]
    exposure            = data["exposure"]
    order_level_scale   = data["order_level_scale"]
    loss_profit_scale   = data["loss_profit_scale"]
    order_cancellation  = data["order_cancellation"]
    order_expiration    = data["order_expiration"]
    order_side          = data["order_side"]
    order_level         = data["order_level"]
    order_TP            = data["order_TP"]
    order_SL            = data["order_SL"]
    trail_profit        = data["trail_profit"]
    trail_SL            = data["trail_SL"]
    order_bigSL         = data["order_bigSL"]
    second_sl           = data["second_sl"]
    manual_sl           = data["manual_sl"]
    trade_periods_h     = data["trade_periods_h"]
    trade_periods_m     = data["trade_periods_m"]
    trade_periods       = data["trade_periods"]
    pending_tolerance   = data["pending_tolerance"]
    stop_tolerance      = data["stop_tolerance"]
    time_offset         = data["time_offset"]
    step_time           = data["step_time"]
    time_frame          = data["time_frame"]
    orphan_limit        = data["orphan_limit"]
settings_file.close()

tick_info = get_tick(pair)


def candle_polling():
    global lblStsCndl
    lblStsCndl.configure(fg='#f66')
    # check time slot with hours
    must_run = False
    if trade_periods == 0:
        for t in range(len(trade_periods_h)):
            t_start = trade_periods_h[t][0].split(":")
            t_start = float(t_start[0]+t_start[1]+t_start[2])
            t_end = trade_periods_h[t][1].split(":")
            t_end = float(t_end[0]+t_end[1]+t_end[2])
            t_now = float(datetime.now(timezone.utc).strftime("%H%M%S"))
            if t_now >= t_start and t_now < t_end:
                must_run = True
        if must_run == False or must_stop == True:
            lblStsCndl.configure(fg='#622')
            return
    else:
    # check time slot minutes only
        for t in range(len(trade_periods_m)):
            t_start = trade_periods_m[t][0].split(":")
            t_start = float(t_start[1]+t_start[2])
            t_end = trade_periods_m[t][1].split(":")
            t_end = float(t_end[1]+t_end[2])
            t_now = float(datetime.now(timezone.utc).strftime("%M%S"))
            if t_now >= t_start and t_now < t_end:
                must_run = True
        if must_run == False or must_stop == True:
            lblStsCndl.configure(fg='#622')
            return

    # exit if there are filled (open) orders from before
    orders = db_read("db_orders", "Orders")["Orders"]
    for order in orders:
        if order["CID"][0] == "p" and order["status"] == "filled": 
            lblStsCndl.configure(fg='#622')
            return

    # exit if all order levels are set to zero
    if sum([abs(x) for x in order_level])==0: 
        lblStsCndl.configure(fg='#622')
        return

    # wait for 0s
    while(int(datetime.now(timezone.utc).strftime("%S")) != time_offset): time.sleep(0.1)

    # get last closed 1-min candle
    candle = get_candle(pair,time_frame)
    last_close = candle["price"]
    if order_size_scale == 0:
        candle_size =  candle["high"] - candle["low"]
        unit = "$"
    else:
        candle_size = (candle["high"] - candle["low"]) / last_close * 100
        unit = "%"

    # check conditions and send order
    if candle_size != 0 and candle_size <= candle_size_max and candle_size >= candle_size_min:
      #log the candle
        db_insert(db_name="db_candles", key="Candles", data={
            "time": candle["time"],
            "pair": pair,
            "symbol": symbol,
            "high": candle["high"],
            "low": candle["low"],
            "last_close": candle["price"],
            "ref_size_min": candle_size_min,
            "ref_size_max": candle_size_max
        })
        # cancel all previous pendings
    else: 
        lblStsCndl.configure(fg='#622')
        return

    # cancel_pending_orders(pair, tick_info["lot_size"])
    cancel_all_orders(pair)
    log_prnt("\n+ Candle size OK (" + str(round(candle_size,2)) + " " + unit + ") at " + datetime.fromtimestamp(candle["time"]/1000+60).strftime("%H:%M:%S"))
    capital = get_account("USDT")["balance"]
    # send new pending (limit) orders
    for o in range(len(order_level)):
        if order_level[o] == 0: continue   # check if the pending order must be sent: level=0 means do not send the order
        # choose high/low price as reference depending on buy/sell
        mark_price = candle["high"] if order_side[o]=="buy" else candle["low"]
        # check leverage
        global leverage
        leverage = min(leverage, tick_info["max_leverage"])
        # set order limit price
        if order_level_scale == 0:
            stop_price = mark_price + order_level[o]
        else:
            stop_price = mark_price * (1 + order_level[o]/100)
        limit_price = stop_price + pending_tolerance[o] if order_side[o] == "buy" else stop_price - pending_tolerance[o]
        limit_price = round(limit_price/tick_info["tick_size"]) * tick_info["tick_size"]
        # set order size
        if order_size_scale == 0:
            order_size = exposure
        else:
            order_size = capital * (exposure/100)
        lot_size = tick_info["lot_size"]
        order_size = round(order_size/stop_price/lot_size*leverage)
        # order_size = 1
        # set SL TP
        if loss_profit_scale == 0:
            sl = stop_price + order_SL[o]
            bsl= stop_price + order_bigSL[o]
            tp = stop_price + order_TP[o]
        else:
            sl = stop_price * (1 + order_SL[o]/100)
            bsl = stop_price * (1 + order_bigSL[o]/100)
            tp = stop_price * (1 + order_TP[o]/100)
        sslx = -1 if order_side[o]=="buy" else 1
        ssl  =   sslx * second_sl + sl
        tsl  = 2*sslx * second_sl + sl

        # order ID
        CID = "p_" + str(round(time.time()*1000))
    # sending order
        R = send_stoplimit_order(symbol=pair, side=order_side[o], leverage=leverage, price=limit_price, size_base=order_size, CID=CID, tolerance=pending_tolerance[o])
        try:
            if R["data"]["orderId"]: ID = R["data"]["orderId"]
            log_prnt(" - Stop limit order: " + order_side[o].capitalize() + " at " + "%.2f"%(round(stop_price,2)) + " $")
        #log the orders
            db_insert("db_orders", key="Orders", data={
                "time1": candle["time"],
                "pair": pair,
                "side": order_side[o],
                "leverage": leverage,
                "price1": stop_price,
                "size": order_size,
                "balance1": capital,
                "sl": sl,
                "bsl": bsl,
                "ssl": ssl,
                "tsl": tsl,
                "tp": tp,
                "CID": CID,
                "status": "pending",
                "api_status": "",
                "id": ID,
                "filled_size": 0,
                "price2": 0,
                "result": 0,
                "time2": 0,
                "time3": 0,
                "o": o
            })
        except Exception as e:
            log_prnt("Error sending stop limit order\n" + str(R) + "\nR: " + str(e))
    lblStsCndl.configure(fg='#622')


def order_status_polling():
    global orphan_found, lblStsState, lblPos
    if int(datetime.now(timezone.utc).strftime("%S")) > 54 or lblStsState.cget('foreground') == '#6f6': return
    print("\n")
    print(time.time())
    lblStsState.configure(fg='#6f6')
    capital = get_account("USDT")["balance"]
    # get the online list of orders from API
    order_list_api = get_all_orders(pair, tick_info["lot_size"])
    print(time.time())
    # get the list of orders from database
    order_list_db = db_read("db_orders", "Orders")["Orders"]
    if len(order_list_db) > 20:
        order_list_db = order_list_db[len(order_list_db)-19:]
    # sync offline and online order list
    for o in range(len(order_list_db)):
        found = False
        oid = order_list_db[o]["CID"]
        for api_order in order_list_api:
            if oid == api_order[0]:
                # print("x")
                found = True
                if order_list_db[o]["api_status"]  != api_order[1]:
                    print("y")
                    order_list_db[o]["api_status"]  = api_order[1]
                    order_list_db[o]["filled_size"] = api_order[2]
                    order_list_db[o]["time2"]       = api_order[3]
                    order_list_db[o]["id"]          = api_order[4]
                    order_list_db[o]["price1"]      = api_order[5]
                    order_list_db[o]["time1"]       = api_order[6]
                    if order_list_db[o]["CID"][0] == "p" and order_list_db[o]["filled_size"] != 0:
                        print("z")
                        filled_price = order_list_db[o]["price1"]
                        q = order_list_db[o]["o"]
                        if loss_profit_scale == 0:
                            sl = filled_price + order_SL[q]
                            bsl= filled_price + order_bigSL[q]
                            tp = filled_price + order_TP[q]
                        else:
                            sl  = filled_price * (1 + order_SL[q]/100)
                            bsl = filled_price * (1 + order_bigSL[q]/100)
                            tp  = filled_price * (1 + order_TP[q]/100)
                        sslx = -1 if order_side[q]=="buy" else 1
                        ssl  =   sslx * second_sl + sl
                        tsl  = 2*sslx * second_sl + sl
                        order_list_db[o]["tp"]          = tp
                        order_list_db[o]["bsl"]         = bsl
                        order_list_db[o]["sl"]          = sl
                        order_list_db[o]["ssl"]         = ssl
                        order_list_db[o]["tsl"]         = tsl
                break
        if found == False:
            order_list_db[o]["api_status"]  = "done"
            order_list_db[o]["filled_size"] = 0
            order_list_db[o]["id"]          = ""

    db_update("db_orders", "Orders", order_list_db)
    print(time.time())

    # find changes
    market_price = get_tick(pair)["price"]
    for o in range(len(order_list_db)):
    # changed from pending to cancelled
        if order_list_db[o]["status"] == "pending" and order_list_db[o]["api_status"] == "done" and order_list_db[o]["filled_size"] == 0:
            order_list_db[o]["status"] = "cancelled"
            db_update_field("db_orders", "Orders", order_list_db[o]["CID"], "status", "cancelled")

    # changed from pending to filled/closed
        if order_list_db[o]["status"] == "pending" and order_list_db[o]["api_status"] == "done" and order_list_db[o]["filled_size"] != 0:
            # update status in db
            order_list_db[o]["status"] = "filled"
            db_update_field("db_orders", "Orders", order_list_db[o]["CID"], "status", "filled")
        # from pending to filled (a pending order was filled)
            if order_list_db[o]["CID"][0]=="p":
                log_prnt("A " + order_list_db[o]["side"] + " order was filled: " + order_list_db[o]["CID"])

                time.sleep(1)

        # send TP
                CIDt = "t_" + order_list_db[o]["CID"][2:]
                tp_side = "sell" if order_list_db[o]["side"] == "buy" else "buy"
                R = send_stoplimit_order(symbol=pair, side=tp_side, leverage=leverage, price=order_list_db[o]["tp"], size_base=order_list_db[o]["size"], CID=CIDt, reduce_only="true", tolerance=stop_tolerance[4])
                try:
                    if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # log_prnt(" - Stop limit order: " + order["side"].capitalize() + " at " + "%.2f"%(round(limit_price,2)) + " $")
                #log the orders
                    db_insert("db_orders", key="Orders", data={
                        "time1": round(time.time()*1000),
                        "pair": pair,
                        "side": tp_side,
                        "leverage": leverage,
                        "price1": order_list_db[o]["tp"],
                        "size": order_list_db[o]["size"],
                        "balance1": capital,
                        "sl": 0,
                        "tp": 0,
                        "CID": CIDt,
                        "status": "pending",
                        "api_status": "",
                        "id": ID,
                        "filled_size": 0,
                        "price2": 0,
                        "result": 0,
                        "time2": 0,
                        "time3": 0
                    })
                except Exception as e:
                    log_prnt("Error sending take-profit order! Manage the open position manually...\nR: "  + str(R) + "\n" + str(e))

        # send SL
                CIDs = "s_" + order_list_db[o]["CID"][2:]
                sl_side = "sell" if order_list_db[o]["side"] == "buy" else "buy"
                R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=order_list_db[o]["sl"], size_base=order_list_db[o]["size"], CID=CIDs, reduce_only="true", tolerance=stop_tolerance[0])
                try:
                    if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # log_prnt(" - Stop limit order: " + order["side"].capitalize() + " at " + "%.2f"%(round(limit_price,2)) + " $")
                #log the orders
                    db_insert("db_orders", key="Orders", data={
                        "time1": round(time.time()*1000),
                        "pair": pair,
                        "side": sl_side,
                        "leverage": leverage,
                        "price1": order_list_db[o]["sl"],
                        "size": order_list_db[o]["size"],
                        "balance1": capital,
                        "sl": 0,
                        "tp": 0,
                        "CID": CIDs,
                        "status": "pending",
                        "api_status": "",
                        "id": ID,
                        "filled_size": 0,
                        "price2": 0,
                        "result": 0,
                        "time2": 0,
                        "time3": 0
                    })
                except Exception as e:
                    log_prnt("Error sending stop-loss order! Manage the open position manually...\nR: "  + str(R) + "\n" + str(e))


                # cancel pendings if cancellation=1
                if order_cancellation == 1:
                    cancel_pending_orders(pair, tick_info["lot_size"])
                    time.sleep(0.1)


        # send big SL
                CIDb = "b_" + order_list_db[o]["CID"][2:]
                R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=order_list_db[o]["bsl"], size_base=order_list_db[o]["size"], CID=CIDb, reduce_only="true", tolerance=stop_tolerance[3])
                try:
                    if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # log_prnt(" - Stop limit order: " + order["side"].capitalize() + " at " + "%.2f"%(round(limit_price,2)) + " $")
                #log the orders
                    db_insert("db_orders", key="Orders", data={
                        "time1": round(time.time()*1000),
                        "pair": pair,
                        "side": sl_side,
                        "leverage": leverage,
                        "price1": order_list_db[o]["bsl"],
                        "size": order_list_db[o]["size"],
                        "balance1": capital,
                        "sl": 0,
                        "tp": 0,
                        "CID": CIDb,
                        "status": "pending",
                        "api_status": "",
                        "id": ID,
                        "filled_size": 0,
                        "price2": 0,
                        "result": 0,
                        "time2": 0,
                        "time3": 0
                    })
                except Exception as e:
                    log_prnt("Error sending big stop-loss order! Manage the open position manually...\nR: "  + str(R) + "\n" + str(e))


        # send second SL
                CIDz = "z_" + order_list_db[o]["CID"][2:]
                R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=order_list_db[o]["ssl"], size_base=order_list_db[o]["size"], CID=CIDz, reduce_only="true", tolerance=stop_tolerance[1])
                try:
                    if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # log_prnt(" - Stop limit order: " + order["side"].capitalize() + " at " + "%.2f"%(round(limit_price,2)) + " $")
                #log the orders
                    db_insert("db_orders", key="Orders", data={
                        "time1": round(time.time()*1000),
                        "pair": pair,
                        "side": sl_side,
                        "leverage": leverage,
                        "price1": order_list_db[o]["ssl"],
                        "size": order_list_db[o]["size"],
                        "balance1": capital,
                        "sl": 0,
                        "tp": 0,
                        "CID": CIDz,
                        "status": "pending",
                        "api_status": "",
                        "id": ID,
                        "filled_size": 0,
                        "price2": 0,
                        "result": 0,
                        "time2": 0,
                        "time3": 0
                    })
                except Exception as e:
                    log_prnt("Error sending second stop-loss order! Manage the open position manually...\nR: "  + str(R) + "\n" + str(e))


        # send third SL
                CIDy = "y_" + order_list_db[o]["CID"][2:]
                R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=order_list_db[o]["tsl"], size_base=order_list_db[o]["size"], CID=CIDy, reduce_only="true", tolerance=stop_tolerance[2])
                try:
                    if R["data"]["orderId"]: ID = R["data"]["orderId"]
                #log the orders
                    db_insert("db_orders", key="Orders", data={
                        "time1": round(time.time()*1000),
                        "pair": pair,
                        "side": sl_side,
                        "leverage": leverage,
                        "price1": order_list_db[o]["tsl"],
                        "size": order_list_db[o]["size"],
                        "balance1": capital,
                        "sl": 0,
                        "tp": 0,
                        "CID": CIDy,
                        "status": "pending",
                        "api_status": "",
                        "id": ID,
                        "filled_size": 0,
                        "price2": 0,
                        "result": 0,
                        "time2": 0,
                        "time3": 0
                    })
                except Exception as e:
                    log_prnt("Error sending third stop-loss order! Manage the open position manually...\nR: "  + str(R) + "\n" + str(e))


        # from pending to closed (a sl/tp order was filled)
            if order_list_db[o]["CID"][0]=="s" or order_list_db[o]["CID"][0]=="t" or order_list_db[o]["CID"][0]=="b" or order_list_db[o]["CID"][0]=="z" or order_list_db[o]["CID"][0]=="y":
                # cancel the opposite order
                if order_list_db[o]["CID"][0]=="s":
                    log_prnt("SL activated: at " + datetime.now().strftime("%H:%M:%S"))
                    oCID1 = "b_"
                    oCID2 = "t_"
                    oCID3 = "z_"
                    oCID4 = "y_"
                if order_list_db[o]["CID"][0]=="b":
                    log_prnt("Big SL activated: at " + datetime.now().strftime("%H:%M:%S"))
                    oCID1 = "s_"
                    oCID2 = "t_"
                    oCID3 = "z_"
                    oCID4 = "y_"
                if order_list_db[o]["CID"][0]=="t":
                    log_prnt("TP activated: at " + datetime.now().strftime("%H:%M:%S"))
                    oCID1 = "s_"
                    oCID2 = "b_"
                    oCID3 = "z_"
                    oCID4 = "y_"
                if order_list_db[o]["CID"][0]=="z":
                    log_prnt("Second SL activated: at " + datetime.now().strftime("%H:%M:%S"))
                    oCID1 = "s_"
                    oCID2 = "b_"
                    oCID3 = "t_"
                    oCID4 = "y_"
                if order_list_db[o]["CID"][0]=="y":
                    log_prnt("Third SL activated: at " + datetime.now().strftime("%H:%M:%S"))
                    oCID1 = "s_"
                    oCID2 = "b_"
                    oCID3 = "t_"
                    oCID4 = "z_"
                oCID1 = oCID1 + order_list_db[o]["CID"][2:]
                oCID2 = oCID2 + order_list_db[o]["CID"][2:]
                oCID3 = oCID3 + order_list_db[o]["CID"][2:]
                oCID4 = oCID4 + order_list_db[o]["CID"][2:]
                cancel_order(db_get_field("db_orders", "Orders", oCID1, "id"))
                cancel_order(db_get_field("db_orders", "Orders", oCID2, "id"))
                cancel_order(db_get_field("db_orders", "Orders", oCID3, "id"))
                cancel_order(db_get_field("db_orders", "Orders", oCID4, "id"))
                # update db
                db_update_field("db_orders", "Orders", "p_"+ order_list_db[o]["CID"][2:], "status", "closed")
                db_update_field("db_orders", "Orders", "p_"+ order_list_db[o]["CID"][2:], "time3",  order_list_db[o]["time2"])
                db_update_field("db_orders", "Orders", "p_"+ order_list_db[o]["CID"][2:], "price2", order_list_db[o]["price1"])
                result = -1 if order_list_db[o]["side"] == "buy" else 1
                result = result * (float(db_get_field("db_orders", "Orders", "p_"+ order_list_db[o]["CID"][2:], "price2")) - \
                        float(db_get_field("db_orders", "Orders", "p_"+ order_list_db[o]["CID"][2:], "price1"))) * \
                        float(db_get_field("db_orders", "Orders", "p_"+ order_list_db[o]["CID"][2:], "filled_size")) * tick_info["lot_size"]
                db_update_field("db_orders", "Orders", "p_"+ order_list_db[o]["CID"][2:], "result", result)   # s: stop loss / t: take profit
                # cancel pendings if cancellation=2 and positive result
                if order_cancellation == 2 and result > 0:
                    cancel_pending_orders(pair, tick_info["lot_size"])

        # log info on the screen
        if o == 0:
            aa.delete(1.0,END)
            order_prnt("Time      Side  Size    Price1      Price2      SL         TP          Market      Status")
            order_prnt("__________________________________________________________________________________________\n")

        if (order_list_db[o]["status"] == "pending" or order_list_db[o]["status"] == "filled" or order_list_db[o]["status"] == "closed") and order_list_db[o]["CID"][0]=="p":
            order_prnt( "" + datetime.fromtimestamp(order_list_db[o]["time1"]/1000).strftime("%H:%M:%S") +
                "  " + order_list_db[o]["side"][0].capitalize() + "     " + "%.1f"%(order_list_db[o]["size"]) +
                "      " + "%.2f"%(round(order_list_db[o]["price1"],2)) + "     " + ("%.2f"%(round(order_list_db[o]["price2"],2))).zfill(7) +
                "     " + "%.2f"%(round(order_list_db[o]["sl"],2)) + "    " + "%.2f"%(round(order_list_db[o]["tp"],2)) +
                "     " + "%.2f"%(round(market_price,2)) +  "     " + order_list_db[o]["status"] #+ "    %.3f"%order_list_db[o]["result"]
            )


    print(time.time())
    # check orphan orders
    if int(datetime.now(timezone.utc).strftime("%S")) > -1:
        order_list_db = db_read("db_orders", "Orders")["Orders"]
        positions = get_positions(pair)
        open_qty = 0
        for position in positions:
            open_qty = open_qty + position["currentQty"]
        sl_qty = 0
        for order in order_list_db:
            if (order["CID"][0] == "s" or order["CID"][0] == "b" or order["CID"][0] == "z" or order["CID"][0] == "y") and order["status"] == "pending":
                s = 1 if order["side"] == "buy" else -1
                sl_qty = sl_qty + s * order["size"]
        lblPos.configure(text = str(open_qty) + " / " + str(sl_qty))
        if open_qty != 0 and open_qty * sl_qty >= 0 and abs(open_qty) > abs(sl_qty):
            side = "buy" if open_qty < 0 else "sell"
            size = round(abs(open_qty - sl_qty/3))
            if orphan_found == 3:
                log_prnt("\n* Orphan position(s) found. Attempting to close...")
                R = send_stoplimit_order( symbol=pair, side=side, leverage=leverage, size_base=size, reduce_only="true", CID = "s_orphan_cancellation1", price=market_price + orphan_limit, tolerance = orphan_limit/2)
                R = send_stoplimit_order( symbol=pair, side=side, leverage=leverage, size_base=size, reduce_only="true", CID = "s_orphan_cancellation1", price=market_price - orphan_limit, tolerance = orphan_limit/2)
                try:
                    if R["data"]["orderId"] != "":
                        log_prnt("  Limit close order sent")
                except Exception as err:
                        log_prnt("  Could not close the position. Handle it manually!\n" + str(err))
                orphan_found = 0
            else:
                orphan_found = orphan_found + 1

        print(time.time())
    # update status of lost positions
        if open_qty == 0:
            for order in order_list_db:
                if order["status"] == "pending" and order["CID"][0] != "p":
                    cancel_order(order["id"])
                    break
            for order in order_list_db:
                if order["status"] == "filled" and order["CID"][0] == "p":
                    db_update_field("db_Orders", 'Orders', order["CID"], "status", "closed")
                    pass
    lblStsState.configure(fg='#262')
    print(time.time())


def order_action_polling():
    global lblStsAction
    if int(datetime.now(timezone.utc).strftime("%S")) > 55 or lblStsAction.cget('foreground') == '#6f6': return
    lblStsAction.configure(fg='#66f')
    orders = db_read("db_orders", "Orders")["Orders"]
    last_price = get_tick(pair)["price"]
    for o in range(len(orders)):
        order = orders[o]
        # check expired pendings
        # if order_cancellation 3: pendings expire after x candles
        if order["CID"][0] == "p" and order["status"] == "pending" and time.time() * 1000 > float(order["time1"]) + 60000 * (order_expiration * time_frame + time_frame) and order["time1"] > 0:
            cancel_pending_orders(pair, tick_info["lot_size"])
            log_prnt("Order expiration activated")

        # check trail levels
        if order["CID"][0] == "p" and order["status"] == "filled":
            dir = 1 if order["side"] == "buy" else -1
            for t in range(len(trail_profit)):
                T = order["price1"] + dir * trail_profit[t] if loss_profit_scale == 0 else order["price1"] * (1 + dir * trail_profit[t] / 100)
                S = order["price1"] + dir * (trail_profit[t] + trail_SL[t])  if loss_profit_scale == 0 else order["price1"] * (100 + dir * (trail_profit[t] + trail_SL[t])) / 100
                # update stop loss
                if dir * (last_price - T) > 0 and ((order["side"] == "buy" and S > order["sl"]) or (order["side"] == "sell" and S < order["sl"])):
                    CIDs = "s_" + order["CID"][2:]
                    CIDz = "z_" + order["CID"][2:]
                    CIDy = "y_" + order["CID"][2:]
                    CIDb = "b_" + order["CID"][2:]
                    cancel_order(db_get_field("db_orders", "Orders", CIDs, "id"))
                    cancel_order(db_get_field("db_orders", "Orders", CIDz, "id"))
                    cancel_order(db_get_field("db_orders", "Orders", CIDy, "id"))
                    cancel_order(db_get_field("db_orders", "Orders", CIDb, "id"))
                    sslx = -1 if order["side"] == "buy" else 1
                    ssl =   sslx * second_sl + S
                    tsl = 2*sslx * second_sl + S
                    bsl = order_bigSL[order["o"]] + tsl
                    order["sl"] = S
                    orders[o]["sl"] = S
                    order["ssl"] = ssl
                    orders[o]["ssl"] = ssl
                    order["tsl"] = tsl
                    orders[o]["tsl"] = tsl
                    order["bsl"] = bsl
                    orders[o]["bsl"] = bsl
                    db_update_field("db_orders", "Orders", order["CID"], "sl", S)
                    db_update_field("db_orders", "Orders", order["CID"], "ssl", ssl)
                    db_update_field("db_orders", "Orders", order["CID"], "tsl", tsl)
                    db_update_field("db_orders", "Orders", order["CID"], "bsl", bsl)
                    sl_side = "sell" if order["side"] == "buy" else "buy"
                    time.sleep(0.1)
                    R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=S, size_base=order["size"], CID=CIDs, reduce_only="true", tolerance=stop_tolerance[0])
                    try:
                        if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # update the sl orders
                        db_update_field("db_orders", "Orders", CIDs, "id"       , ID)
                        db_update_field("db_orders", "Orders", CIDs, "price1"   , S)
                        db_update_field("db_orders", "Orders", CIDs, "status"   , "pending")
                    except Exception as e:
                        log_prnt("Error trailing the order! Manage the open position manually...\n" + str(R))
                    R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=ssl, size_base=order["size"], CID=CIDz, reduce_only="true", tolerance=stop_tolerance[1])
                    try:
                        if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # update the ssl orders
                        db_update_field("db_orders", "Orders", CIDz, "id"    , ID)
                        db_update_field("db_orders", "Orders", CIDz, "price1", ssl)
                        db_update_field("db_orders", "Orders", CIDz, "status", "pending")
                    except Exception as e:
                        log_prnt("Error trailing the order! Manage the open position manually...\n" + str(R))
                    R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=tsl, size_base=order["size"], CID=CIDy, reduce_only="true", tolerance=stop_tolerance[2])
                    try:
                        if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # update the tsl orders
                        db_update_field("db_orders", "Orders", CIDy, "id"    , ID)
                        db_update_field("db_orders", "Orders", CIDy, "price1", tsl)
                        db_update_field("db_orders", "Orders", CIDy, "status", "pending")
                    except Exception as e:
                        log_prnt("Error trailing the order! Manage the open position manually...\n" + str(R))
                    R = send_stoplimit_order(symbol=pair, side=sl_side, leverage=leverage, price=bsl, size_base=order["size"], CID=CIDb, reduce_only="true", tolerance=stop_tolerance[3])
                    try:
                        if R["data"]["orderId"]: ID = R["data"]["orderId"]
                    # update the tsl orders
                        db_update_field("db_orders", "Orders", CIDb, "id"    , ID)
                        db_update_field("db_orders", "Orders", CIDb, "price1", bsl)
                        db_update_field("db_orders", "Orders", CIDb, "status", "pending")
                    except Exception as e:
                        log_prnt("Error trailing the order! Manage the open position manually...\n" + str(R))
                    unit = "$" if order_size_scale == 0 else "%"
                    log_prnt("Trailing at " + str(trail_profit[t]) + unit + " profit: new SL " + str(S))
                    # break
        # manual SL
            if ((order["side"] == "buy" and last_price < order["sl"] - manual_sl) or (order["side"] == "sell" and last_price > order["sl"] + manual_sl)):
                sl_side = "sell" if order["side"] == "buy" else "buy"
                R = send_market_order(symbol=pair, side=sl_side, leverage=leverage, size_base=order["size"], reduce_only="true", CID="manual_SL")
                db_update_field("db_orders", "Orders", "s_" + order["CID"][2:], "status", "closed")
                db_update_field("db_orders", "Orders", "s_" + order["CID"][2:], "filled_size", order["size"])
                log_prnt("Manual SL activated!")
    lblStsAction.configure(fg='#226')


def cancel_pending_orders(pair, lot_size):
    orders = get_all_orders(pair, lot_size)
    if len(orders) == 0: return 
    for order in orders:
        try:
            if order[0][0] != "t" and order[0][0] != "s" and order[0][0] != "b" and order[0][0] != "z" and order[0][0] != "y":
                (cancel_order(order[4]))
        except Exception as err:
            (cancel_order(order[4]))


def cancel_everything(pair):
    cancel_all_orders(pair)
    close_positions()


def cancel_stop_orders(pair, lot_size):
    # cancel_all_orders(pair)
    orders = get_all_orders(pair, lot_size)
    if len(orders) == 0: return 
    for order in orders:
        try:
            if order[0][0] != "p":
                (cancel_order(order[4]))
        except Exception as err:
            (cancel_order(order[4]))


def close_positions():
    positions = get_positions(pair)
    open_qty = 0
    for position in positions:
        open_qty = open_qty + position["currentQty"]
    if open_qty == 0: return
    side = "sell" if open_qty > 0 else "buy"
    R = send_market_order(symbol=pair, side=side, leverage=leverage, size_base=abs(open_qty), reduce_only="true", CID="close_all_positions")
    try:
        if R["data"]["orderId"] != "":
            log_prnt("  Market close order sent")
    except Exception as err:
            log_prnt("  Could not close the position. Handle it manually!\n" + str(err))


def save_api():
    global e1,e2,e3
    api_key = e1.get()
    api_secret = e2.get()
    api_passphrase = e3.get()
    try:
        with open(".env","w") as env:
            env.write("api_key = " + api_key)
            env.write("\napi_secret = " + api_secret)
            env.write("\napi_passphrase = " + api_passphrase)
            exit()
    except Exception as err:
        print("Cannot save the file:\n" + str(err))


def report():
    global h1, d1, m1, y1, h2, d2, m2, y2, frame, pair
    frame.load_html("<body bgcolor='#222'><font color='#ccc'><h3>Please wait...<br>Getting data from the server...</h3></font></body>")
    sh1 = str(min([23,int(h1.get())]))
    sd1 = d1.get()
    sm1 = m1.get()
    sy1 = y1.get()
    sh2 = str(min([23,int(h2.get())]))
    sd2 = d2.get()
    sm2 = m2.get()
    sy2 = y2.get()
    if len(sh1) == 1: sh1 = "0" + str(sh1)
    if len(sd1) == 1: sd1 = "0" + str(sd1)
    if len(sm1) == 1: sm1 = "0" + str(sm1)
    if len(sh2) == 1: sh2 = "0" + str(sh2)
    if len(sd2) == 1: sd2 = "0" + str(sd2)
    if len(sm2) == 1: sm2 = "0" + str(sm2)
    start_time = time.mktime(datetime.strptime(str(sh1)+"0000"+str(sd1)+str(sm1)+str(sy1), "%H%M%S%d%m%Y").timetuple())
    end_time   = time.mktime(datetime.strptime(str(sh2)+"5959"+str(sd2)+str(sm2)+str(sy2), "%H%M%S%d%m%Y").timetuple())
    Rep = get_report(pair,int(start_time),int(end_time))
    # print(Rep)
    Report = "<html><head><title>Detailed trade report</title><link rel='stylesheet' href='style.css'></head><body bgcolor='#222'>"\
            + "<table width=95% align=center dir=ltr id=T1 border=1 name=T1 class='blueTable'><thead align=center><tr>"\
            + "<th>Total number of trades</th><th>Profit without commisions</th><th>Commisions</th> "\
            + "</tr></thead><tbody align=center>"\
            + "<tr><td>" + str(int(Rep[0])) + "</td><td>" + str(round(Rep[1],3)) + "</td>"\
            + "<td>" + str(round(Rep[2],3)) + "</tr></tbody></table><br> &nbsp;<br>"\
            + "<table width=95% align=center dir=ltr id=T1 border=1 name=T1 class='blueTable'><thead align=center><tr>"\
            + "<th>Profit - commisions</th><th>Average commision per trade</th></tr></thead><tbody align=center>"\
            + "<td>" + str(round(Rep[3],3)) + "</td>"\
            + "<td>" + str(round(Rep[2]/(Rep[0]+0.001),3)) + "</td></tr></tbody></table>"\
            + "</html>"
    frame.load_html("<pre>" + Report)


def trend():
    global h1, d1, m1, y1, h2, d2, m2, y2, frame, pair
    frame.load_html("<body bgcolor='#222'><font color='#ccc'><h3>Please wait...<br>Getting data from the server...</h3></font></body>")
    sh1 = str(min([23,int(h1.get())]))
    sd1 = d1.get()
    sm1 = m1.get()
    sy1 = y1.get()
    sh2 = str(min([23,int(h2.get())]))
    sd2 = d2.get()
    sm2 = m2.get()
    sy2 = y2.get()
    if len(sh1) == 1: sh1 = "0" + str(sh1)
    if len(sd1) == 1: sd1 = "0" + str(sd1)
    if len(sm1) == 1: sm1 = "0" + str(sm1)
    if len(sh2) == 1: sh2 = "0" + str(sh2)
    if len(sd2) == 1: sd2 = "0" + str(sd2)
    if len(sm2) == 1: sm2 = "0" + str(sm2)
    start_time = time.mktime(datetime.strptime(str(sh1)+"0000"+str(sd1)+str(sm1)+str(sy1), "%H%M%S%d%m%Y").timetuple())
    end_time   = time.mktime(datetime.strptime(str(sh2)+"5959"+str(sd2)+str(sm2)+str(sy2), "%H%M%S%d%m%Y").timetuple())
    Rep = get_report(pair,int(start_time),int(end_time),True)
    Rep = Rep[::-1]

    if len(Rep) == 0:
        frame.load_html("<body bgcolor='#222'><font color='#ccc'><h3>No trades found in this period!</h3></font></body>")
        return

    Rep2 = Rep
    for row in Rep2: row["x"] = 0

    win = 0
    lose = 0

    cap = [[100, datetime.fromtimestamp(Rep[0]["tradeTime"]/1000000000).strftime("%d/%m/%Y  %H:%M:%S")]]
    pos = 0
    for n in range(len(Rep2)):
        if Rep2[n]["size"] == Rep2[n]["x"]: continue
        for m in range(len(Rep2[n:])):
            if Rep2[n]["side"] != Rep2[m]["side"] and Rep2[m]["x"] < Rep2[m]["size"]:
                if Rep2[n]["size"] - Rep2[n]["x"] <= Rep2[m]["size"] - Rep2[m]["x"]:
                    vol = Rep2[n]["size"] - Rep2[n]["x"]
                    Rep2[m]["x"] = Rep2[m]["x"] + (Rep2[n]["size"] - Rep2[n]["x"])
                    Rep2[n]["x"]  = Rep2[n]["size"]
                    dir = 1 if Rep2[n]["side"] == "buy" else -1
                    profit = 1 + dir * (float(Rep2[m]["price"]) - float(Rep2[n]["price"])) / float(Rep2[n]["price"]) * leverage * vol
                    if profit > 1: win = win + 1
                    else: lose = lose + 1
                    cap.append([cap[-1][0] * profit, datetime.fromtimestamp(Rep2[m]["tradeTime"]/1000000000).strftime("%d/%m/%Y  %H:%M:%S")])
                    break
                else:
                    vol = Rep2[m]["size"] - Rep2[m]["x"]
                    Rep2[m]["x"] = Rep2[m]["size"]
                    Rep2[n]["x"]  = Rep2[n]["x"]  + (Rep2[m]["size"] - Rep2[m]["x"])
                    dir = 1 if Rep2[n]["side"] == "buy" else -1
                    profit = 1 + dir * (float(Rep2[m]["price"]) - float(Rep2[n]["price"])) / float(Rep2[n]["price"]) * leverage * vol
                    if profit > 1: win = win +1
                    else: lose = lose + 1
                    cap.append([cap[-1][0] * profit, datetime.fromtimestamp(Rep2[m]["tradeTime"]/1000000000).strftime("%d/%m/%Y  %H:%M:%S")])
                    if Rep2[n]["x"] == Rep2[n]["size"]: break

    print(len(Rep2)/2, len(cap))



    DF = pandas.DataFrame(cap)
    DF.columns = ["Capital", "Time"]
    fig = px.line(DF, x="Time", y="Capital", title="Capital trend")
    fig.show()

    drawdown = []
    capx = [row[0] for row in cap]
    for n in range(len(capx)):
        if capx[n] == max(capx[:n+1]):
            drawdown.append((capx[n] - min(capx[n+1:]))/capx[n])
    frame.load_html("<body bgcolor='#222' align=center><font color='#ccc'><h3>Maximum drawdown: " + str(round(max(drawdown)*100,1)) + " %" +\
                    "<br/><br/>Wins: " + str(win) + "<br/><br/>Loses: " + str(lose) + "<br/><br/>Success rate: " + str(round(win/(win+lose)*100,1)) + "%</h3></font></body>")


def detailed_report():
    global h1, d1, m1, y1, h2, d2, m2, y2, frame, pair
    frame.load_html("<body bgcolor='#222'><font color='#ccc'><h3>Please wait...<br>Getting data from the server...</h3></font></body>")
    sh1 = str(min([23,int(h1.get())]))
    sd1 = d1.get()
    sm1 = m1.get()
    sy1 = y1.get()
    sh2 = str(min([23,int(h2.get())]))
    sd2 = d2.get()
    sm2 = m2.get()
    sy2 = y2.get()
    if len(sh1) == 1: sh1 = "0" + str(sh1)
    if len(sd1) == 1: sd1 = "0" + str(sd1)
    if len(sm1) == 1: sm1 = "0" + str(sm1)
    if len(sh2) == 1: sh2 = "0" + str(sh2)
    if len(sd2) == 1: sd2 = "0" + str(sd2)
    if len(sm2) == 1: sm2 = "0" + str(sm2)
    start_time = time.mktime(datetime.strptime(str(sh1)+"0000"+str(sd1)+str(sm1)+str(sy1), "%H%M%S%d%m%Y").timetuple())
    end_time   = time.mktime(datetime.strptime(str(sh2)+"5959"+str(sd2)+str(sm2)+str(sy2), "%H%M%S%d%m%Y").timetuple())
    Rep = get_report(pair,int(start_time),int(end_time),True)
    report = "<html><head><title>Detailed trade report</title><link rel='stylesheet' href='style.css'></head><body bgcolor='#222'>"\
            + "<table width=95% align=center dir=ltr id=T1 border=1 name=T1 class='blueTable'><thead align=center><tr>"\
            + "<th>Open time</th> <th>Side</th> <th>Price</th> <th>Size</th> <th>Finish time</th></tr></thead><tbody align=center>"
    for n in range(len(Rep)):
        row = Rep[n]
        report = report + "<tr><td>" + datetime.fromtimestamp(row["createdAt"]/1000).strftime("%d/%m/%Y  %H:%M:%S") + "</td>"\
                + "<td>" + row["side"].capitalize() + "</td>"\
                + "<td>" + str(row["price"]) + "</td>"\
                + "<td>" + str(row["size"]) + "</td>"\
                + "<td>" + datetime.fromtimestamp(row["tradeTime"]/1000000000).strftime("%d/%m/%Y  %H:%M:%S") + "</td></tr>"
    report = report + "</tbody></table></html>"
    frame.load_html(report)


def clear_db():
    db_update("db_orders",  "Orders",  [])
    db_update("db_candles", "Candles", [])


def clear_scr():
    aa.delete(1.0,END)
    bb.delete(1.0,END)


def runClock():
    global lblClk
    while True:
        lblClk.configure(text = datetime.now(timezone.utc).strftime("%H:%M:%S"))
        time.sleep(0.25)


def runbot():
    bb.delete(1.0,END)
    global must_stop
    log_prnt("Starting the bot...")
    btnStart["state"] = "disabled"
    btnStop["state"] = "normal"
    btnReset["state"] = "disabled"
    for i in range(0,60000):
        if must_stop:
            btnStart["state"] = "normal"
            btnStop["state"] = "disabled"
            btnReset["state"] = "normal"
            must_stop = False
            return
        read_settings()
        order_status_polling()
        if int(datetime.now(timezone.utc).strftime("%S")) > 55 - step_time and int(datetime.now(timezone.utc).strftime("%M"))%time_frame == time_frame-1:
            candle_polling()
            order_status_polling()
        order_action_polling()

        time.sleep(step_time)


def stop_bot():
    global must_stop
    log_prnt("\nStopping the bot... please wait")
    log_prnt("There might be open orders on your account. You have to manage them manually...")
    must_stop = True


def runThread(func):
    submit_thread = threading.Thread(target=func)
    submit_thread.daemon = True
    submit_thread.start()

def splash():
    for i in range(10):
        time.sleep(0.05)
    splash_root.destroy()

splash_root = Tk()
splash_root.geometry("600x338")
splash_root.overrideredirect(True)
splash_image = tk.PhotoImage(file="splash.png")
ttk.Label(splash_root, image=splash_image).grid(sticky="news")
splash_root.after(1000,splash)
splash_root.eval('tk::PlaceWindow . center')
mainloop()
time.sleep(0.5)

orphan_found = 0
mainRT = Tk()
mainRT.configure(background='#222')
mainRT.resizable(False, False) 
mainRT.title("KuCoin Trading Bot")

noteStyle = ttk.Style()
noteStyle.theme_use('default')
noteStyle.configure("TNotebook", background="#222", borderwidth=3)
noteStyle.configure(".", background="#222")
noteStyle.configure("TNotebook.Tab", background="#999", borderwidth=1)

tabs = ttk.Notebook(mainRT)
tab1 = ttk.Frame(tabs)
tabs.add(tab1, text = "  Run the bot  ")
tab2 = ttk.Frame(tabs)
tabs.add(tab2, text = "     Reports     ")
tab4 = ttk.Frame(tabs)
tabs.add(tab4, text = " API settings ")
tabs.pack(expand=1, fill = 'both')
tab3 = ttk.Frame(tabs)

Label(tab1,text="Open order state:", fg="#999", bg="#222", font='Lucida 9 bold').grid(row=0, column=0, sticky="w", padx=2, pady=1)
lblClk = Label(tab1,text="00:00:00", fg="#999", bg="#222", font='Lucida 9 bold')
lblClk.grid(row=0, column=6, sticky="e", padx=16, pady=2)
lblPos = Label(tab1,text="? / ?", fg="#999", bg="#222", font='Tahoma 9 bold')
lblPos.grid(row=0, column=2, sticky="e", padx=80, pady=2)
lblStsCndl = Label(tab1,text="●", fg='#622', font=10, bg="#222")
lblStsCndl.grid(row=0, column=2, sticky="e", padx=50, pady=2)
lblStsState = Label(tab1,text="●", fg='#262', font=10, bg="#222")
lblStsState.grid(row=0, column=2, sticky="e", padx=30, pady=2)
lblStsAction = Label(tab1,text="●", fg='#226', font=10, bg="#222")
lblStsAction.grid(row=0, column=2, sticky="e", padx=10, pady=2)
aa = scrolledtext.ScrolledText(tab1,width=65,height=10, fg="#ddd", bg="#333")
aa.grid(row=1,column=0,sticky="we",columnspan=7, padx=2, pady=1)
# aa.bind("<Key>", lambda e: "break")
Label(tab1,text="What is happening:", fg="#999", bg="#222", font='Tahoma 9 bold').grid(row=2, column=0, sticky="w", padx=2, pady=5)
bb = scrolledtext.ScrolledText(tab1,width=65,height=30, fg="#ddd", bg="#333")
bb.grid(row=3,column=0,sticky="we",columnspan=7, padx=2, pady=1)
# bb.bind("<Key>", lambda e: "break")
btnStart = Button(tab1, text="   Start!   ", padx=10, pady=2 , command=lambda: runThread(runbot), fg="#999", bg="#222", font='Lucida 9 bold')
btnStart.grid(row=4,column=0,pady=2,padx=5)
btnStop = Button(tab1, text="     Stop     ", padx=10, pady=2 , command=lambda: runThread(stop_bot), state="disabled", fg="#999", bg="#222", font='Lucida 9 bold')
btnStop.grid(row=4,column=1,pady=2,padx=5)
btnCancel = Button(tab1, text="Cancel pendings", padx=10, pady=2 , command=lambda: cancel_pending_orders(pair, tick_info["lot_size"]), fg="#999", bg="#222", font='Lucida 9 bold')
btnCancel.grid(row=4,column=2,pady=2,padx=5)
btnClose = Button(tab1, text="Close positions", padx=10, pady=2 , command=lambda: runThread(close_positions), fg="#999", bg="#222", font='Lucida 9 bold')
btnClose.grid(row=4,column=3,pady=2,padx=5)
btnReset = Button(tab1, text=" Reset DB ", padx=10, pady=2 , command=lambda: clear_db(), fg="#999", bg="#222", font='Lucida 9 bold')
btnReset.grid(row=4,column=4,pady=2,padx=5)
btnClear = Button(tab1, text="   Clear   ", padx=10, pady=2 , command=lambda: clear_scr(), fg="#999", bg="#222", font='Lucida 9 bold')
btnClear.grid(row=4,column=5,pady=10,padx=5)
btnAll = Button(tab1, text=" Close all ", padx=10, pady=2 , command=lambda: cancel_everything(pair), fg="#999", bg="#222", font='Lucida 9 bold')
btnAll.grid(row=4,column=6,pady=10,padx=5)


l1 = tk.Label(tab2, text="Start date GMT (HH D/M/Y)", fg="#999", bg="#222", font='Tahoma 9 bold').grid(row=0, column=0, sticky = "e",pady=10,padx=10)
h1 = tk.Entry(tab2, width=3, fg="#300", bg="#ccc", font='Lucida 9 bold')
d1 = tk.Entry(tab2, width=3, fg="#300", bg="#ccc", font='Lucida 9 bold')
m1 = tk.Entry(tab2, width=3, fg="#300", bg="#ccc", font='Lucida 9 bold')
y1 = tk.Entry(tab2, width=5, fg="#300", bg="#ccc", font='Lucida 9 bold')
h1.grid(row=0, column=1, sticky = "w",pady=10,padx=10)
d1.grid(row=0, column=2, sticky = "w",pady=10,padx=10)
m1.grid(row=0, column=3, sticky = "w",pady=10,padx=10)
y1.grid(row=0, column=4, sticky = "w",pady=10,padx=10)
h1.insert(END,int(datetime.now(timezone.utc).strftime("%H")))
d1.insert(END,int(datetime.now(timezone.utc).strftime("%d")))
m1.insert(END,datetime.now(timezone.utc).strftime("%m"))
y1.insert(END,datetime.now(timezone.utc).strftime("%Y"))
l2 = tk.Label(tab2, text="End date GMT (HH D/M/Y)", fg="#999", bg="#222", font='Tahoma 9 bold').grid(row=1, column=0, sticky = "e",pady=10,padx=10)
h2 = tk.Entry(tab2, width=3, fg="#300", bg="#ccc", font='Lucida 9 bold')
d2 = tk.Entry(tab2, width=3, fg="#300", bg="#ccc", font='Lucida 9 bold')
m2 = tk.Entry(tab2, width=3, fg="#300", bg="#ccc", font='Lucida 9 bold')
y2 = tk.Entry(tab2, width=5, fg="#300", bg="#ccc", font='Lucida 9 bold')
h2.grid(row=1, column=1, sticky = "w",pady=10,padx=10)
d2.grid(row=1, column=2, sticky = "w",pady=10,padx=10)
m2.grid(row=1, column=3, sticky = "w",pady=10,padx=10)
y2.grid(row=1, column=4, sticky = "w",pady=10,padx=10)
h2.insert(END,int(datetime.now(timezone.utc).strftime("%H")))
d2.insert(END,int(datetime.now(timezone.utc).strftime("%d")))
m2.insert(END,datetime.now(timezone.utc).strftime("%m"))
y2.insert(END,datetime.now(timezone.utc).strftime("%Y"))
Button(tab2, text="Get report", padx=10, pady=2 , command=lambda: runThread(report), fg="#999", bg="#222", font='Lucida 9 bold').grid(row=2,column=0,columnspan=1,pady=10,padx=10,sticky="we")
Button(tab2, text="View details", padx=10, pady=2 , command=lambda: runThread(detailed_report), fg="#999", bg="#222", font='Lucida 9 bold').grid(row=2,column=1,columnspan=2,pady=10,padx=10,sticky="we")
Button(tab2, text="View trend", padx=10, pady=2 , command=lambda: runThread(trend), fg="#999", bg="#222", font='Lucida 9 bold').grid(row=2,column=3,columnspan=2,pady=10,padx=10,sticky="we")
frame = HtmlFrame(tab2,height=200,width=200,messages_enabled = False)
frame.grid(row=3,column=0,columnspan=5)


l1 = tk.Label(tab4, text="API KEY", fg="#999", bg="#222", font='Lucida 9 bold').grid(row=0, column=0, sticky = "e",pady=10,padx=10)
l2 = tk.Label(tab4, text="API SECRET", fg="#999", bg="#222", font='Lucida 9 bold').grid(row=1, column=0, sticky = "e",pady=10,padx=10)
l3 = tk.Label(tab4, text="API PASSPHRASE", fg="#999", bg="#222", font='Lucida 9 bold').grid(row=2, column=0, sticky = "e",pady=10,padx=10)
e1 = tk.Entry(tab4, width=50, fg="#300", bg="#ccc", font='Lucida 9 bold')
e2 = tk.Entry(tab4, width=50, fg="#300", bg="#ccc", font='Lucida 9 bold')
e3 = tk.Entry(tab4, width=50, fg="#300", bg="#ccc", font='Lucida 9 bold')
e1.grid(row=0, column=1, sticky = "w",pady=10,padx=10)
e2.grid(row=1, column=1, sticky = "w",pady=10,padx=10)
e3.grid(row=2, column=1, sticky = "w",pady=10,padx=10)
Button(tab4, text=" Save API settings ", padx=10, pady=2 , command=save_api, fg="#999", bg="#222", font='Lucida 9 bold').grid(row=3,column=0,columnspan=2,pady=10,padx=10)
Label(tab4, text="After saving the API settings, the bot will close. You need to start it again to work with the new API keys.",\
     fg="#999", bg="#222", font='Lucida 9 bold').grid(row=4, column=0, columnspan=2, sticky = "e", pady=10, padx=10)


must_stop = False
try:
    runThread(runClock)
except Exception as err:
    runThread(runClock)


mainRT.eval('tk::PlaceWindow . center')
mainloop()