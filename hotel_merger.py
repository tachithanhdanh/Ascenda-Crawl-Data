from dataclasses import dataclass
import json
import argparse

import requests


@dataclass
class Location:
    lat: float
    lng: float
    address: str
    city: str
    country: str


@dataclass
class Amenities:
    general: list[str]
    room: list[str]


@dataclass
class Image:
    link: str
    description: str


@dataclass
class Images:
    rooms: list[Image]
    site: list[Image]
    amenities: list[Image]


@dataclass
class Hotel:
    id: str
    destination_id: str
    name: str
    description: str
    location: Location
    amenities: Amenities
    images: Images
    booking_conditions: list[str]


class BaseSupplier:
    def endpoint():
        """URL to fetch supplier data"""

    def parse(obj: dict) -> Hotel:
        """Parse supplier-provided data into Hotel object"""

    def fetch(self):
        url = self.endpoint()
        resp = requests.get(url)
        return [self.parse(dto) for dto in resp.json()]


class Acme(BaseSupplier):
    @staticmethod
    def endpoint():
        return "https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/acme"

    @staticmethod
    def parse(dto: dict) -> Hotel:
        return Hotel(
            id=dto["Id"],
            destination_id=dto["DestinationId"],
            name=dto["Name"],
            description=dto["Description"],
            location=Location(
                lat=dto["Latitude"],
                lng=dto["Longitude"],
                address=dto["Address"],
                city=dto["City"],
                country=dto["Country"],
            ),
            amenities=Amenities(
                general=dto["Facilities"],
                room=[],
            ),
            images=Images(
                rooms=[],
                site=[],
                amenities=[],
            ),
            booking_conditions=[],
        )


class Patagonia(BaseSupplier):
    @staticmethod
    def endpoint():
        return "https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/patagonia"

    @staticmethod
    def parse(dto: dict) -> Hotel:
        return Hotel(
            id=dto["id"],
            destination_id=dto["destination"],
            name=dto["name"],
            description=dto["info"],
            location=Location(
                lat=dto["lat"],
                lng=dto["lng"],
                address=dto["address"],
                city="",
                country="",
            ),
            amenities=Amenities(
                room=dto["amenities"],
                general=[],
            ),
            images=Images(
                site=[],  # No site images in Patagonia data
                rooms=[
                    Image(
                        link=room["url"],
                        description=room["description"],
                    )
                    for room in dto["images"]["rooms"]
                ],
                amenities=[
                    Image(
                        link=amenity["url"],
                        description=amenity["description"],
                    )
                    for amenity in dto["images"]["amenities"]
                ],
            ),
            booking_conditions=[],
        )


class Paperflies(BaseSupplier):
    @staticmethod
    def endpoint():
        return "https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/paperflies"

    @staticmethod
    def parse(dto: dict) -> Hotel:
        return Hotel(
            id=dto["hotel_id"],
            destination_id=dto["destination_id"],
            name=dto["hotel_name"],
            description=dto["details"],
            location=Location(
                lat="",
                lng="",
                city="",
                address=dto["location"]["address"],
                country=dto["location"]["country"],
            ),
            amenities=Amenities(
                general=dto["amenities"]["general"],
                room=dto["amenities"]["room"],
            ),
            images=Images(
                rooms=[
                    Image(
                        link=room["link"],
                        description=room["caption"],
                    )
                    for room in dto["images"]["rooms"]
                ],
                site=[
                    Image(
                        link=site["link"],
                        description=site["caption"],
                    )
                    for site in dto["images"]["site"]
                ],
                amenities=[],  # No amenities images in Paperflies data
            ),
            booking_conditions=dto["booking_conditions"],
        )


class HotelsService:
    def __init__(self):
        self.data = []

    def merge_value(self, value1, value2):
        """Helper function to merge two values based on conditions."""
        if value1 is None and value2 is None:
            return None
        elif value1 is None:
            return value2
        elif value2 is None:
            return value1
        else:
            return value1 if len(str(value1)) >= len(str(value2)) else value2

    def merge_and_save(self, hotels: list[Hotel]):
        merged_hotels: dict[str, Hotel] = {}

        for hotel in hotels:
            key = (hotel.id, hotel.destination_id)

            if key not in merged_hotels:
                merged_hotels[key] = hotel
            else:
                existing = merged_hotels[key]

                # Merge name and description
                existing.name = self.merge_value(existing.name, hotel.name)
                existing.description = self.merge_value(
                    existing.description, hotel.description
                )

                # Merge location fields
                existing.location.lat = self.merge_value(
                    existing.location.lat, hotel.location.lat
                )
                existing.location.lng = self.merge_value(
                    existing.location.lng, hotel.location.lng
                )
                existing.location.address = self.merge_value(
                    existing.location.address, hotel.location.address
                )
                existing.location.city = self.merge_value(
                    existing.location.city, hotel.location.city
                )
                existing.location.country = self.merge_value(
                    existing.location.country, hotel.location.country
                )

                # Merge amenities
                existing.amenities.general = self.merge_value(
                    existing.amenities.general, hotel.amenities.general
                )
                existing.amenities.room = self.merge_value(
                    existing.amenities.room, hotel.amenities.room
                )

                # Merge images
                existing.images.rooms = self.merge_value(
                    existing.images.rooms, hotel.images.rooms
                )
                existing.images.site = self.merge_value(
                    existing.images.site, hotel.images.site
                )
                existing.images.amenities = self.merge_value(
                    existing.images.amenities, hotel.images.amenities
                )

                # Merge booking conditions
                existing.booking_conditions = self.merge_value(
                    existing.booking_conditions, hotel.booking_conditions
                )

        self.data = list(merged_hotels.values())

    def find(self, hotel_ids, destination_ids):
        # return list of hotel objects such that hotels.hotel_id == hotel_ids[i] and hotels.destination_id == destination_ids[i]
        # cast destination_ids as a list of str
        hotel_ids = [] if hotel_ids == "none" else hotel_ids.split(",")
        destination_ids = (
            [] if destination_ids == "none" else destination_ids.split(",")
        )
        # print(hotel_ids, destination_ids)
        if (len(hotel_ids) == 0) or (len(destination_ids) == 0):
            return self.data
        return [
            hotel
            for hotel in self.data
            if str(hotel.id) in hotel_ids
            and str(hotel.destination_id) in destination_ids
        ]


def custom_hotel_serializer(hotel):
    return {
        "id": hotel.id,
        "destination_id": hotel.destination_id,
        "name": hotel.name,
        "location": {
            "lat": hotel.location.lat,
            "lng": hotel.location.lng,
            "address": hotel.location.address,
            "city": hotel.location.city,
            "country": hotel.location.country,
        },
        "description": hotel.description,
        "amenities": {"general": hotel.amenities.general, "room": hotel.amenities.room},
        "images": {
            "rooms": [
                {"link": room.link, "description": room.description}
                for room in hotel.images.rooms
            ],
            "site": [
                {"link": site.link, "description": site.description}
                for site in hotel.images.site
            ],
            "amenities": [
                {"link": amenity.link, "description": amenity.description}
                for amenity in hotel.images.amenities
            ],
        },
        "booking_conditions": hotel.booking_conditions,
    }


def fetch_hotels(hotel_ids, destination_ids):
    # Write your code here

    suppliers: list[BaseSupplier] = [
        Acme(),
        Paperflies(),
        Patagonia(),
    ]

    # Fetch data from all suppliers
    all_supplier_data = []
    for supplier in suppliers:
        supplier_hotel = supplier.fetch()
        all_supplier_data.extend(supplier_hotel)
        # print(supplier_hotel)

    # Merge all the data and save it in-memory somewhere
    svc = HotelsService()
    svc.merge_and_save(all_supplier_data)

    # Fetch filtered data
    filtered = svc.find(hotel_ids, destination_ids)

    # Return as json
    return json.dumps([custom_hotel_serializer(hotel) for hotel in filtered], indent=2)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("hotel_ids", type=str, help="Hotel IDs")
    parser.add_argument("destination_ids", type=str, help="Destination IDs")

    # Parse the arguments
    args = parser.parse_args()

    hotel_ids = args.hotel_ids
    destination_ids = args.destination_ids

    result = fetch_hotels(hotel_ids, destination_ids)
    print(result)


if __name__ == "__main__":
    main()
