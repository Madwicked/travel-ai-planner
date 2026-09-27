import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.hotel_content import HotelContent
from app.models.hotel_room import HotelRoom
from app.services.hotel_content import HotelContentProvider


class HotelContentService:
    def __init__(
        self,
        db: Session,
        provider: HotelContentProvider,
    ):
        self.db = db
        self.provider = provider

    def _get_facility_map(
            self,
            language: str = "ENG",
    ) -> dict[tuple[str, str], str]:
        data = self.provider.get_facilities(
            language=language,
        )

        facilities = data.get(
            "facilities",
            [],
        )

        facility_map = {}

        for facility in facilities:
            code = facility.get("code")
            group_code = facility.get(
                "facilityGroupCode"
            )

            description = facility.get(
                "description"
            )

            if isinstance(description, dict):
                description = description.get(
                    "content"
                )

            if code is None or group_code is None:
                continue

            if not description:
                continue

            facility_map[
                (
                    str(code),
                    str(group_code),
                )
            ] = str(description)

        return facility_map

    def _enrich_room_facilities(
            self,
            rooms: list,
            facility_map: dict[tuple[str, str], str],
    ) -> list:
        enriched_rooms = []

        for room in rooms:
            room_copy = dict(room)

            room_facilities = []

            for facility in room.get(
                    "roomFacilities",
                    [],
            ):
                facility_copy = dict(facility)

                key = (
                    str(
                        facility.get(
                            "facilityCode"
                        )
                    ),
                    str(
                        facility.get(
                            "facilityGroupCode"
                        )
                    ),
                )

                description = facility_map.get(key)

                if description:
                    facility_copy[
                        "description"
                    ] = description

                room_facilities.append(
                    facility_copy
                )

            room_copy[
                "roomFacilities"
            ] = room_facilities

            room_stays = []

            for room_stay in room.get(
                    "roomStays",
                    [],
            ):
                stay_copy = dict(room_stay)

                stay_facilities = []

                for facility in room_stay.get(
                        "roomStayFacilities",
                        [],
                ):
                    facility_copy = dict(
                        facility
                    )

                    key = (
                        str(
                            facility.get(
                                "facilityCode"
                            )
                        ),
                        str(
                            facility.get(
                                "facilityGroupCode"
                            )
                        ),
                    )

                    description = facility_map.get(
                        key
                    )

                    if description:
                        facility_copy[
                            "description"
                        ] = description

                    stay_facilities.append(
                        facility_copy
                    )

                stay_copy[
                    "roomStayFacilities"
                ] = stay_facilities

                room_stays.append(
                    stay_copy
                )

            room_copy[
                "roomStays"
            ] = room_stays

            enriched_rooms.append(
                room_copy
            )

        return enriched_rooms

    def _sync_hotel_rooms(
        self,
        hotel: HotelContent,
        rooms: list,
    ) -> None:
        self.db.query(HotelRoom).filter(
            HotelRoom.hotel_content_id == hotel.id
        ).delete(
            synchronize_session=False
        )

        for room in rooms:
            room_code = str(
                room.get("roomCode", "")
            ).strip()

            if not room_code:
                continue

            hotel_room = HotelRoom(
                hotel_content_id=hotel.id,
                room_code=room_code,
                room_type=self._get_string(
                    room.get("roomType")
                ),
                characteristic_code=self._get_string(
                    room.get("characteristicCode")
                ),
                pms_room_code=self._get_string(
                    room.get("PMSRoomCode")
                ),
                min_pax=room.get("minPax"),
                max_pax=room.get("maxPax"),
                max_adults=room.get("maxAdults"),
                max_children=room.get("maxChildren"),
                room_facilities=json.dumps(
                    room.get("roomFacilities", []),
                    ensure_ascii=False,
                ),
                room_stays=json.dumps(
                    room.get("roomStays", []),
                    ensure_ascii=False,
                ),
            )

            self.db.add(hotel_room)

    def _sync_hotel_rooms(
        self,
        hotel: HotelContent,
        rooms: list,
    ) -> None:
        self.db.query(HotelRoom).filter(
            HotelRoom.hotel_content_id == hotel.id
        ).delete(
            synchronize_session=False
        )

        for room in rooms:
            room_code = str(
                room.get("roomCode", "")
            ).strip()

            if not room_code:
                continue

            hotel_room = HotelRoom(
                hotel_content_id=hotel.id,
                room_code=room_code,
                room_type=self._get_string(
                    room.get("roomType")
                ),
                characteristic_code=self._get_string(
                    room.get("characteristicCode")
                ),
                pms_room_code=self._get_string(
                    room.get("PMSRoomCode")
                ),
                min_pax=room.get("minPax"),
                max_pax=room.get("maxPax"),
                max_adults=room.get("maxAdults"),
                max_children=room.get("maxChildren"),
                room_facilities=json.dumps(
                    room.get("roomFacilities", []),
                    ensure_ascii=False,
                ),
                room_stays=json.dumps(
                    room.get("roomStays", []),
                    ensure_ascii=False,
                ),
            )

            self.db.add(hotel_room)

    def sync_hotels(
            self,
            language: str = "ENG",
            hotel_code: str | None = None,
    ) -> int:
        if hotel_code:
            data = self.provider.get_hotel(
                hotel_code=hotel_code,
                language=language,
            )

            hotels = data.get("hotels", [])

            if not hotels:
                return 0

            facility_map = self._get_facility_map(
                language=language,
            )

            for hotel_data in hotels:
                rooms = hotel_data.get(
                    "rooms",
                    [],
                )

                hotel_data["rooms"] = (
                    self._enrich_room_facilities(
                        rooms,
                        facility_map,
                    )
                )

            if not hotels:
                return 0

            hotel_data = hotels[0]

            code = str(
                hotel_data.get("code")
            ).strip()

            if not code:
                return 0

            hotel = (
                self.db.query(HotelContent)
                .filter(
                    HotelContent.hotel_code == code
                )
                .first()
            )

            if hotel is None:
                hotel = HotelContent(
                    hotel_code=code,
                )
                self.db.add(hotel)

            self._update_hotel(
                hotel,
                hotel_data,
            )

            self.db.add(hotel)
            self.db.flush()

            self._sync_hotel_rooms(
                hotel,
                hotel_data.get("rooms", []),
            )

            self.db.commit()

            return 1

        hotels = self.provider.get_all_hotels(
            language=language,
        )

        saved_count = 0

        for hotel_data in hotels:
            hotel_code = str(
                hotel_data.get("code")
            ).strip()

            if not hotel_code:
                continue

            hotel = (
                self.db.query(HotelContent)
                .filter(
                    HotelContent.hotel_code == hotel_code
                )
                .first()
            )

            if hotel is None:
                hotel = HotelContent(
                    hotel_code=hotel_code,
                )
                self.db.add(hotel)

            self._update_hotel(
                hotel,
                hotel_data,
            )

            saved_count += 1

        self.db.commit()

        return saved_count

    def sync_updated_hotels(
        self,
        last_update_time: str,
        language: str = "ENG",
    ) -> int:
        hotels = self.provider.get_updated_hotels(
            last_update_time=last_update_time,
            language=language,
        )

        saved_count = 0

        for hotel_data in hotels:
            hotel_code = str(
                hotel_data.get("code")
            ).strip()

            if not hotel_code:
                continue

            hotel = (
                self.db.query(HotelContent)
                .filter(
                    HotelContent.hotel_code == hotel_code
                )
                .first()
            )

            if hotel is None:
                hotel = HotelContent(
                    hotel_code=hotel_code,
                )
                self.db.add(hotel)

            self._update_hotel(
                hotel,
                hotel_data,
            )

            saved_count += 1

        self.db.commit()

        return saved_count

    @staticmethod
    def _update_hotel(
            hotel: HotelContent,
            data: dict[str, Any],
    ) -> None:
        hotel.name = (
            HotelContentService._get_string(
                data.get("name")
            )
        )

        hotel.category_code = (
            HotelContentService._get_string(
                data.get("categoryCode")
            )
        )

        hotel.category_name = (
            HotelContentService._get_string(
                data.get("categoryName")
            )
        )

        hotel.accommodation_type = (
            HotelContentService._get_accommodation_type(
                data
            )
        )

        hotel.country_code = (
            HotelContentService._get_country_code(
                data
            )
        )

        hotel.destination_code = (
            HotelContentService._get_string(
                data.get("destinationCode")
            )
        )

        hotel.zone_code = (
            HotelContentService._get_string(
                data.get("zoneCode")
            )
        )

        hotel.city = (
            HotelContentService._get_city(
                data
            )
        )

        hotel.address = (
            HotelContentService._get_address(
                data
            )
        )

        hotel.latitude = (
            HotelContentService._get_coordinate(
                data.get("latitude")
            )
        )

        hotel.longitude = (
            HotelContentService._get_coordinate(
                data.get("longitude")
            )
        )

        hotel.description = (
            HotelContentService._get_description(
                data
            )
        )

        facilities = data.get(
            "facilities",
            [],
        )

        hotel.facilities = json.dumps(
            facilities,
            ensure_ascii=False,
        )

        rooms = data.get(
            "rooms",
            [],
        )

        hotel.rooms = json.dumps(
            rooms,
            ensure_ascii=False,
        )

        hotel.pets_allowed = (
            HotelContentService._detect_pets(
                facilities
            )
        )

        hotel.adults_only = (
            HotelContentService._detect_adults_only(
                data,
                facilities,
            )
        )

    @staticmethod
    def _get_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        if isinstance(value, dict):
            value = (
                value.get("content")
                or value.get("name")
                or value.get("code")
                or value.get("value")
            )

        if value is None:
            return None

        return str(value)

    @staticmethod
    def _get_accommodation_type(
        data: dict[str, Any],
    ) -> str | None:
        category = data.get(
            "category",
            {},
        )

        if isinstance(category, dict):
            accommodation_type = category.get(
                "accommodationType"
            )

            if accommodation_type:
                return str(
                    accommodation_type
                )

        accommodation_type = data.get(
            "accommodationType"
        )

        if accommodation_type:
            return str(
                accommodation_type
            )

        return None

    @staticmethod
    def _get_country_code(
        data: dict[str, Any],
    ) -> str | None:
        country = data.get(
            "country",
            {},
        )

        if isinstance(country, dict):
            code = country.get("code")

            if code:
                return str(code)

        code = data.get(
            "countryCode"
        )

        if code:
            return str(code)

        return None

    @staticmethod
    def _get_city(
        data: dict[str, Any],
    ) -> str | None:
        city = data.get(
            "city",
            {}
        )

        if isinstance(city, dict):
            content = city.get(
                "content"
            )

            if content:
                return str(content)

            name = city.get("name")

            if name:
                return str(name)

        if isinstance(city, str):
            return city

        destination = data.get(
            "destination",
            {}
        )

        if isinstance(destination, dict):
            name = destination.get("name")

            if name:
                return str(name)

        return None

    @staticmethod
    def _get_address(
        data: dict[str, Any],
    ) -> str | None:
        address = data.get(
            "address",
            {}
        )

        if isinstance(address, dict):
            content = address.get(
                "content"
            )

            if content:
                return str(content)

            value = address.get(
                "value"
            )

            if value:
                return str(value)

        if isinstance(address, str):
            return address

        return None
    @staticmethod
    def _get_coordinate(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        if isinstance(value, list):
            if not value:
                return None

            value = value[0]

        if isinstance(value, dict):
            value = (
                value.get("content")
                or value.get("value")
            )

        if value is None:
            return None

        try:
            return str(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_description(
        data: dict[str, Any],
    ) -> str | None:
        descriptions = data.get(
            "description",
            {}
        )

        if isinstance(descriptions, dict):
            content = descriptions.get(
                "content"
            )

            if content:
                return str(content)

        if isinstance(descriptions, str):
            return descriptions

        return None

    @staticmethod
    def _detect_pets(
        facilities: list[Any],
    ) -> bool | None:
        if not facilities:
            return None

        text_parts: list[str] = []

        for facility in facilities:
            if isinstance(facility, dict):
                text_parts.extend(
                    str(value).lower()
                    for value in facility.values()
                    if value is not None
                )

        text = " ".join(text_parts)

        if not text:
            return None

        pet_words = (
            "pet",
            "pets",
            "dog",
            "dogs",
            "cat",
            "cats",
        )

        if any(
            word in text
            for word in pet_words
        ):
            return True

        return None

    @staticmethod
    def _detect_adults_only(
        data: dict[str, Any],
        facilities: list[Any],
    ) -> bool | None:
        text_parts: list[str] = [
            str(data).lower()
        ]

        for facility in facilities:
            if isinstance(facility, dict):
                text_parts.extend(
                    str(value).lower()
                    for value in facility.values()
                    if value is not None
                )

        text = " ".join(text_parts)

        adults_only_words = (
            "adults only",
            "adults-only",
            "adult only",
            "adult-only",
        )

        if any(
            phrase in text
            for phrase in adults_only_words
        ):
            return True

        return None