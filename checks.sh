#!/bin/bash
RES=`sqlite3 drinkingBuddy.db "select id,name,quantity,price from inventory where minquantity > quantity"`
 if [ "$RES" != "" ]; then
   echo $RES
 else
	echo NULL
 fi
