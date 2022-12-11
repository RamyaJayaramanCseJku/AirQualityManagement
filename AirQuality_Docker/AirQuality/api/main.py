from asyncio.log import logger
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from session import db_Session, settings
from schema import UserDetails, Room, Airqualityproperty
from fastAPI_models import UserInfoBase, UserCreate, Token, UserAuthenticate, Room_Object, Update_RoomObject, AirQuality_Properties_Object, AirQuality_Co2_Object, AirQuality_Temperature_Object, AirQuality_Humidity_Object
from typing import List
import bcrypt
import auth

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

tags_metadata = [
    {
        "name": "Users",
        "description": "CRUD operations on room",
    },
    {
        "name": "Rooms",
        "description": "CRUD operations on room",
    },
    {
        "name": "AirQuality",
        "description": "CRUD operations on air quality measurements (co2, temperature and humidity) in room",
    },
]
app = FastAPI(title=settings.PROJECT_NAME,
              version=settings.PROJECT_VERSION, openapi_tags=tags_metadata)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/users/register", status_code=201, response_model=UserInfoBase, tags=["Users"])
def register_user(user: UserCreate):
    db_user = get_user_by_username(username=user.username)
    if db_user:
        raise HTTPException(
            status_code=409, detail="Username already registered")
    return create_user(user=user)


def get_user_by_username(username: str):
    return db_Session.query(UserDetails).filter(UserDetails.username == username).first()


def create_user(user: UserCreate):
    hashed_password = bcrypt.hashpw(
        user.password.encode('utf8'), bcrypt.gensalt())
    hashed_password = hashed_password.decode('utf8')
    db_user = UserDetails(username=user.username,
                          user_password=hashed_password)
    try:
        db_Session.add(db_user)
        db_Session.flush()
        db_Session.commit()
    except Exception as ex:
        logger.error(f"{ex.__class__.__name__}: {ex}")
        db_Session.rollback()
    return db_user


@app.post("/users/authenticate", response_model=Token, tags=["Users"])
def authenticate_user(user: UserAuthenticate):
    db_user = get_user_by_username(username=user.username)
    if db_user is None:
        raise HTTPException(status_code=403, detail="Username is incorrect")
    else:
        is_password_correct = auth.check_username_password(user)
        if is_password_correct is False:
            raise HTTPException(
                status_code=403, detail="password is incorrect")
        else:
            from datetime import timedelta
            access_token_expires = timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = auth.encode_jwt_token(
                data={"sub": user.username}, expires_delta=access_token_expires)
            return {"access_token": access_token, "token_type": "Bearer"}


# Rooms
"""Creates a new room in the database and returns the room on success. Room_id needs to be unique"""
"""Example room object 
{
    "room_id": 1,
    "room_size": 50,
    "people_count":1,
    "measurement_unit":"50 sq.m"
}"""


@app.post("/Rooms", tags=["Rooms"], response_model=Room_Object, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_201_CREATED)
async def add_Room(addRoom: Room_Object):
    db_classes = Room(room_id=addRoom.room_id, room_size=addRoom.room_size,
                      people_count=addRoom.people_count, measurement_unit=addRoom.measurement_unit)
    try:
        db_Session.add(db_classes)
        db_Session.flush()
        db_Session.commit()
    except Exception as ex:
        logger.error(f"{ex.__class__.__name__}: {ex}")
        db_Session.rollback()
    return addRoom

"""Returns all the rooms present in the database"""


@app.get("/Rooms", tags=["Rooms"], response_model=List[Room_Object], status_code=status.HTTP_200_OK, dependencies=[Depends(auth.JWTBearer())])
async def get_AllRoom_Details():
    results = db_Session.query(Room).all()
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No rooms are available')
    else:
        return results

"""Returns a room with a certain room_id or an error if the room does not exist"""


@app.get("/Rooms/{room_id}", tags=["Rooms"], response_model=Room_Object, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_200_OK)
async def get_Specific_Room(room_id: str):
    specificRoomDetail = db_Session.query(
        Room).filter(Room.room_id == room_id).first()
    if not specificRoomDetail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Room with the id {room_id} does not exist')
    else:
        return specificRoomDetail

"""Updates a room with a certain room_id or returns an error if the room does not exist"""


@app.patch("/Rooms/{room_id}", tags=["Rooms"], response_model=Update_RoomObject, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_200_OK)
async def update_RoomDetails(room_id: str, request: Update_RoomObject):
    updateRoomDetail = db_Session.query(
        Room).filter(Room.room_id == room_id).first()
    if not updateRoomDetail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Room with the id {room_id} is not available')
    room_data = request.dict(exclude_unset=True)
    for key, value in room_data.items():
        setattr(updateRoomDetail, key, value)
    db_Session.add(updateRoomDetail)
    db_Session.commit()
    db_Session.refresh(updateRoomDetail)
    return updateRoomDetail

"""Deletes a room with a certain room_id or returns an error if the room does not exist"""


@app.delete("/Rooms/{room_id}", tags=["Rooms"], dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_200_OK)
async def delete_Room(room_id: str):
    deleteRoom = db_Session.query(Room).filter(Room.room_id == room_id).first()
    if not deleteRoom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Room with the room id {room_id} is not found')
    db_Session.delete(deleteRoom)
    db_Session.commit()
    return {"code": "success", "message": f"deleted room with id {room_id}"}

# Air Quality APIs - airQualityinRoom


@app.post("/Room/AirQuality/", tags=["AirQuality"], response_model=AirQuality_Properties_Object, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_201_CREATED)
async def add_AirQuality_Properties(addAirQuality: AirQuality_Properties_Object):
    db_AQP = Airqualityproperty(room_id=addAirQuality.room_id, device_id=addAirQuality.device_id, ventilator=addAirQuality.ventilator, co2=addAirQuality.co2, co2measurementunit=addAirQuality.co2measurementunit,
                                temperature=addAirQuality.temperature, temperaturemeasurementunit=addAirQuality.temperaturemeasurementunit, humidity=addAirQuality.humidity, humiditymeasurementunit=addAirQuality.humiditymeasurementunit, time=addAirQuality.time)
    try:
        db_Session.add(db_AQP)
        db_Session.flush()
        db_Session.commit()
    except Exception as ex:
        logger.error(f"{ex.__class__.__name__}: {ex}")
        db_Session.rollback()
    return addAirQuality


@app.get("/Room/{room_id}/AirQuality/", tags=["AirQuality"], response_model=AirQuality_Properties_Object, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_200_OK)
async def get_AirQuality_Rooms(room_id: str):
    filteredAQPResults = db_Session.query(Airqualityproperty).filter(
        Airqualityproperty.room_id == room_id)
    AQPresults = filteredAQPResults.order_by(
        Airqualityproperty.time.desc()).first()
    if not AQPresults:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No air quality measurements available for the room {room_id}')
    else:
        return AQPresults


@app.get("/Room/{room_id}/AirQuality/temperature/", tags=["AirQuality"], response_model=AirQuality_Temperature_Object, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_200_OK)
async def get_AirQuality_Temperature(room_id: str):
    filteredAQTResults = db_Session.query(Airqualityproperty).filter(
        Airqualityproperty.room_id == room_id)
    AQPTemperature = filteredAQTResults.order_by(
        Airqualityproperty.time.desc()).first()
    if not AQPTemperature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No temperature data available for room id {room_id}')
    else:
        return AQPTemperature


@app.get("/Room/{room_id}/AirQuality/humidity/", tags=["AirQuality"], response_model=AirQuality_Humidity_Object, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_200_OK)
async def get_AirQuality_Humidity(room_id: str):
    filteredAQHResults = db_Session.query(Airqualityproperty).filter(
        Airqualityproperty.room_id == room_id)
    AQPHumidity = filteredAQHResults.order_by(
        Airqualityproperty.time.desc()).first()
    if not AQPHumidity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No humidity data available for room id {room_id}')
    else:
        return AQPHumidity


@app.get("/Room/{room_id}/AirQuality/co2/", tags=["AirQuality"], response_model=AirQuality_Co2_Object, dependencies=[Depends(auth.JWTBearer())], status_code=status.HTTP_200_OK)
async def get_AirQuality_Co2(room_id: str):
    filteredAQCo2Results = db_Session.query(Airqualityproperty).filter(
        Airqualityproperty.room_id == room_id)
    AQPCo2 = filteredAQCo2Results.order_by(
        Airqualityproperty.time.desc()).first()
    if not AQPCo2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No co2 data available for room id {room_id}')
    else:
        return AQPCo2
