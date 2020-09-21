from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from pymongo import MongoClient
# import dns

# to handle CORS error
from flask_cors import CORS

# handle .env
# from dotenv import load_dotenv

# handle "_id" field from string
from bson.objectid import ObjectId

app = Flask(__name__)
CORS(app)
api = Api(app)

client = MongoClient("mongodb+srv://user1:karbonna50@cluster0.vgjcl.mongodb.net/CardsDB?retryWrites=true&w=majority")
db = client["CardDB"]
cards = db["cards"]

# !!!!!!!
# get -> find_one -> ObjectId(next) but its originally objectid type



# task
# pending, completed
# is_pending True (in db)
# new endpoint to mark complete
# /mark-complete/<id>

class AllCards(Resource):

    # Create
    # (title, content)
    # iterate ll and find last

    # edit
    # patch request
    # query paran -> /<id>
    # body -> (new title, desc) any one which is present

    def post(self):
        # body params: array of cards "cards"
        posted_data = request.get_json()
        
        # find last element 
        tail = cards.find_one({"next_id": None})

        # empty card list
        if(not tail):
            result = cards.insert_one({
                "prev_id": None,
                "next_id": None,
                "is_head": True,
                "title": posted_data["title"],
                "content": posted_data["content"],
                "is_pending": True
            })
        else:
            result = cards.insert_one({
                "prev_id": tail["_id"],
                "next_id": None,
                "is_head": False,
                "title": posted_data["title"],
                "content": posted_data["content"],
                "is_pending": True
            })
            # make changes in last element in DB
            cards.update_one(
                {"_id": tail["_id"]}, 
                {"$set": {"next_id": result.inserted_id}}
            )
        
        return jsonify({
            "_id": str(result["_id"]),
            "status": 200,
            "msg": "item added successfully"
        })


    # Read all
    def get(self):
        card_list = []
        cursor = cards.find_one({"is_head": True})
        
        if(not cursor):
            return jsonify({
                "card_list": [],
                "status": 201,
                "msg": "empty todo list"
            })

        while(cursor):
            card_list.append({
                "_id": str(cursor["_id"]),
                "prev_id": str(cursor["prev_id"]) if cursor["prev_id"] else None,
                "next_id": str(cursor["next_id"]) if cursor["next_id"] else None,
                "is_head": cursor["is_head"],
                "title": cursor["title"],
                "content": cursor["content"],
                "is_pending": cursor["is_pending"]
            })

            if(not cursor["next_id"]):
                break
            # move to next
            cursor = cards.find_one({"_id": ObjectId(cursor["next_id"])})

        return jsonify({
            "card_list": card_list,
            "status": 200,
            "msg": "todo list fetched successfully"
        })


    # Update ordering
    def put(self):
        posted_data = request.get_json()
        pred_id = posted_data["pred_id"]    # predecessor of moved position
        cur_id = posted_data["cur_id"]    # element which is moved

        cur_card = cards.find_one({"_id": ObjectId(cur_id)})
        if(not cur_card):
            return jsonify({
                "status": 404,
                "msg": "current element not found"
            })

        # if no movement took place
        if(not cur_card["prev_id"] and not pred_id)\
        or (cur_card["prev_id"] == ObjectId(pred_id))\
        or (cur_card["_id"] == ObjectId(pred_id)):
            return jsonify({
                "status": 201,
                "msg": "nothing to change"
            })

        # change links of prev, next of initial position
        if(not cur_card["prev_id"]):
            cards.update_one(
                {"_id": cur_card["next_id"]},
                {"$set": {
                    "prev_id": None,
                    "is_head": True
                }}
            )
            cards.update_one(
                {"_id": ObjectId(cur_id)},
                {"$set": {"is_head": False}}
            )
        elif(not cur_card["next_id"]):
            cards.update_one(
                {"_id": cur_card["prev_id"]},
                {"$set": {"next_id": None}}
            )
        else:
            prev_id = cur_card["prev_id"]    # prev of initial pos
            next_id = cur_card["next_id"]    # next of initial pos

            cards.update_one(
                {"_id": prev_id},
                {"$set": {"next_id": next_id}}
            )
            cards.update_one(
                {"_id": next_id},
                {"$set": {"prev_id": prev_id}}
            )

        # change links of pred, succ of final position
        if(not pred_id):
            # move to head
            successor = cards.find_one({"is_head": True})
            cards.update_one(
                {"_id": ObjectId(cur_id)},
                {"$set": {
                    "is_head": True,
                    "next_id": successor["_id"],
                    "prev_id": None
                }}
            )
            cards.update_one(
                {"_id": ObjectId(successor["_id"])},
                {"$set": {
                    "is_head": False,
                    "prev_id": ObjectId(cur_id)
                }}
            )

            return jsonify({
                "status": 200,
                "msg": "updated successfully"
            })
        
        predecessor = cards.find_one({"_id": ObjectId(pred_id)})
        if(not predecessor["next_id"]):
            # move to tail
            cards.update_one(
                {"_id": ObjectId(cur_id)},
                {"$set": {
                    "prev_id": predecessor["_id"],
                    "next_id": None
                }}
            )
            cards.update_one(
                {"_id": predecessor["_id"]},
                {"$set": {"next_id": ObjectId(cur_id)}}
            )
        else:
            # move to middle
            cards.update_one(
                {"_id": ObjectId(cur_id)},
                {"$set": {
                    "prev_id": predecessor["_id"],
                    "next_id": predecessor["next_id"]
                }}
            )
            cards.update_one(
                {"_id": predecessor["next_id"]},
                {"$set": {"prev_id": ObjectId(cur_id)}}
            )
            cards.update_one(
                {"_id": predecessor["_id"]},
                {"$set": {"next_id": ObjectId(cur_id)}}
            )

        return jsonify({
            "status": 200,
            "msg": "updated successfully"
        })



class CurCard(Resource):

    # def patch(self, card_id):


    # delete a card
    # /<id>
    def delete(self, card_id):
        if(not card_id):
            return jsonify({
                "status": "404",
                "msg": "no card selected"
            })
        card = cards.find_one({"_id": ObjectId(card_id)})
        if(not card):
            return jsonify({
                "status": 404,
                "msg": "card not found"
            })

        # if single element in link list
        if(not card["prev_id"] and not card["next_id"]):
            pass
        # if it's head
        elif(not card["prev_id"]):
            cards.update_one(
                {"_id": card["next_id"]}, 
                {"$set": {
                    "prev_id": None,
                    "is_head": True
                }}
            )
        # if it's tail
        elif(not card["next_id"]):
            cards.update_one({"_id": card["prev_id"]}, 
                             {"$set": {"next_id": None}})
        else:
            cards.update_one({"_id": card["prev_id"]}, 
                             {"$set": {"next_id": card["next_id"]}})
            cards.update_one({"_id": card["next_id"]}, 
                             {"$set": {"prev_id": card["prev_id"]}})

        cards.delete_one({"_id": ObjectId(card_id)})

        return jsonify({
            "status": 200,
            "msg": "card deleted successfully"
        })


class MarkComplete(Resource):

    def patch(self, card_id):
        cards.update_one(
            {"_id": ObjectId(card_id)},
            {"$set": {"is_pending": False}}
        )

        return jsonify({
            "status": 200
        })


api.add_resource(AllCards, "/")
api.add_resource(CurCard, "/<card_id>")
api.add_resource(MarkComplete, "/mark-complete/<card_id>")

if __name__ == "__main__":
    app.run(port = 5000)