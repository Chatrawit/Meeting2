from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
import os
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure
load_dotenv()

# Initialize MongoDB client with error handling
try:
    client = MongoClient(os.getenv('MONGODB_URL'), serverSelectionTimeoutMS=5000)
    # Verify connection
    client.server_info()
    db = client[os.getenv('DATABASE_NAME')]
    meetings_collection = db["meeting"]
    place_collection = db["place"]
except ConnectionFailure:
    raise Exception("Failed to connect to MongoDB. Please check your connection settings.")
except Exception as e:
    raise Exception(f"Error initializing MongoDB: {str(e)}")

# ... existing code ... 

@router.get("/meeting-counts")
async def get_meeting_counts():
    """
    Get counts of total, upcoming, past, and today's meetings.
    """
    try:
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        today_end = today_start + timedelta(days=1)

        # Use aggregation pipeline for better performance
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "upcoming": [{"$match": {"start_datetime": {"$gt": now}}}, {"$count": "count"}],
                    "past": [{"$match": {"end_datetime": {"$lt": now}}}, {"$count": "count"}],
                    "today": [{"$match": {
                        "start_datetime": {"$gte": today_start},
                        "end_datetime": {"$lt": today_end}
                    }}, {"$count": "count"}]
                }
            }
        ]

        result = list(meetings_collection.aggregate(pipeline))[0]
        
        return MeetingCountResponse(
            total=result["total"][0]["count"] if result["total"] else 0,
            upcoming=result["upcoming"][0]["count"] if result["upcoming"] else 0,
            past=result["past"][0]["count"] if result["past"] else 0,
            today=result["today"][0]["count"] if result["today"] else 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve meeting counts: {str(e)}")

@router.get("/time-distribution")
async def get_meeting_time_distribution(days: int = 90):
    """
    Get distribution of meetings by day of week and hour of day.
    
    Args:
        days: Number of past days to include in analysis
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Use aggregation pipeline for better performance
        pipeline = [
            {
                "$match": {
                    "start_datetime": {"$gte": start_date}
                }
            },
            {
                "$facet": {
                    "by_day": [
                        {
                            "$group": {
                                "_id": {"$dayOfWeek": "$start_datetime"},
                                "count": {"$sum": 1}
                            }
                        },
                        {
                            "$project": {
                                "name": {
                                    "$switch": {
                                        "branches": [
                                            {"case": {"$eq": ["$_id", 1]}, "then": "Monday"},
                                            {"case": {"$eq": ["$_id", 2]}, "then": "Tuesday"},
                                            {"case": {"$eq": ["$_id", 3]}, "then": "Wednesday"},
                                            {"case": {"$eq": ["$_id", 4]}, "then": "Thursday"},
                                            {"case": {"$eq": ["$_id", 5]}, "then": "Friday"},
                                            {"case": {"$eq": ["$_id", 6]}, "then": "Saturday"},
                                            {"case": {"$eq": ["$_id", 7]}, "then": "Sunday"}
                                        ],
                                        "default": "Unknown"
                                    }
                                },
                                "count": 1,
                                "_id": 0
                            }
                        }
                    ],
                    "by_hour": [
                        {
                            "$group": {
                                "_id": {"$hour": "$start_datetime"},
                                "count": {"$sum": 1}
                            }
                        },
                        {
                            "$project": {
                                "name": {
                                    "$concat": [
                                        {"$toString": "$_id"},
                                        ":00"
                                    ]
                                },
                                "count": 1,
                                "_id": 0
                            }
                        }
                    ]
                }
            }
        ]

        result = list(meetings_collection.aggregate(pipeline))[0]
        
        return MeetingTimeDistribution(
            by_day_of_week=result["by_day"],
            by_hour_of_day=result["by_hour"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve time distribution: {str(e)}")

@router.get("/venue-usage")
async def get_venue_usage(limit: int = 10):
    """
    Get most frequently used meeting venues.
    
    Args:
        limit: Number of top venues to return
    """
    try:
        # Optimize venue usage query with aggregation pipeline
        pipeline = [
            {
                "$group": {
                    "_id": "$place_id",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": limit
            },
            {
                "$lookup": {
                    "from": "place",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "place_info"
                }
            },
            {
                "$unwind": "$place_info"
            },
            {
                "$project": {
                    "place_id": "$_id",
                    "place_name": {"$ifNull": ["$place_info.name", "Unknown Venue"]},
                    "meeting_count": "$count",
                    "_id": 0
                }
            }
        ]
        
        result = list(meetings_collection.aggregate(pipeline))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve venue usage: {str(e)}")

@router.get("/overview")
async def get_dashboard_overview():
    """
    Get a comprehensive dashboard overview with key metrics.
    Returns aggregated data from multiple endpoints for a quick summary.
    """
    try:
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        today_end = today_start + timedelta(days=1)
        this_week_end = now + timedelta(days=7)
        
        # Use aggregation pipeline for better performance
        pipeline = [
            {
                "$facet": {
                    "meeting_stats": [
                        {
                            "$facet": {
                                "total": [{"$count": "count"}],
                                "upcoming": [{"$match": {"start_datetime": {"$gt": now}}}, {"$count": "count"}],
                                "past": [{"$match": {"end_datetime": {"$lt": now}}}, {"$count": "count"}],
                                "today": [{"$match": {
                                    "start_datetime": {"$gte": today_start},
                                    "end_datetime": {"$lt": today_end}
                                }}, {"$count": "count"}]
                            }
                        }
                    ],
                    "upcoming_meetings": [
                        {
                            "$match": {
                                "start_datetime": {"$gte": now, "$lte": this_week_end}
                            }
                        },
                        {"$sort": {"start_datetime": 1}},
                        {"$limit": 5},
                        {
                            "$project": {
                                "id": {"$toString": "$_id"},
                                "name": 1,
                                "start_datetime": 1,
                                "end_datetime": 1,
                                "place_id": 1,
                                "_id": 0
                            }
                        }
                    ],
                    "top_venues": [
                        {
                            "$group": {
                                "_id": "$place_id",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"count": -1}},
                        {"$limit": 3},
                        {
                            "$lookup": {
                                "from": "place",
                                "localField": "_id",
                                "foreignField": "_id",
                                "as": "place_info"
                            }
                        },
                        {"$unwind": "$place_info"},
                        {
                            "$project": {
                                "place_id": "$_id",
                                "place_name": {"$ifNull": ["$place_info.name", "Unknown Venue"]},
                                "meeting_count": "$count",
                                "_id": 0
                            }
                        }
                    ],
                    "top_users": [
                        {
                            "$group": {
                                "_id": "$user_create",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"count": -1}},
                        {"$limit": 3},
                        {
                            "$project": {
                                "user_id": "$_id",
                                "meeting_count": "$count",
                                "_id": 0
                            }
                        }
                    ]
                }
            }
        ]

        result = list(meetings_collection.aggregate(pipeline))[0]
        
        # Format meeting stats
        meeting_stats = {
            "total": result["meeting_stats"][0]["total"][0]["count"] if result["meeting_stats"][0]["total"] else 0,
            "upcoming": result["meeting_stats"][0]["upcoming"][0]["count"] if result["meeting_stats"][0]["upcoming"] else 0,
            "past": result["meeting_stats"][0]["past"][0]["count"] if result["meeting_stats"][0]["past"] else 0,
            "today": result["meeting_stats"][0]["today"][0]["count"] if result["meeting_stats"][0]["today"] else 0
        }
        
        return {
            "meeting_stats": meeting_stats,
            "upcoming_meetings": result["upcoming_meetings"],
            "top_venues": result["top_venues"],
            "top_users": result["top_users"],
            "last_updated": now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard overview: {str(e)}")

# ... existing code ... 