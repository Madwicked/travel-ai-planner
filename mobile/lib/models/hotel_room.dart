class HotelRoomFacility {
  final String description;
  final int? number;
  final bool? indFee;
  final bool? indYesOrNo;

  HotelRoomFacility({
    required this.description,
    this.number,
    this.indFee,
    this.indYesOrNo,
  });

  factory HotelRoomFacility.fromJson(Map<String, dynamic> json) {
    return HotelRoomFacility(
      description:
          json['description']?.toString() ??
          json['facilityCode']?.toString() ??
          '',
      number: json['number'] is num ? (json['number'] as num).toInt() : null,
      indFee: json['indFee'] as bool?,
      indYesOrNo: json['indYesOrNo'] as bool?,
    );
  }
}

class HotelRoomStayFacility {
  final String description;
  final int? number;

  HotelRoomStayFacility({required this.description, this.number});

  factory HotelRoomStayFacility.fromJson(Map<String, dynamic> json) {
    return HotelRoomStayFacility(
      description:
          json['description']?.toString() ??
          json['facilityCode']?.toString() ??
          '',
      number: json['number'] is num ? (json['number'] as num).toInt() : null,
    );
  }
}

class HotelRoomStay {
  final String stayType;
  final String description;
  final List<HotelRoomStayFacility> facilities;

  HotelRoomStay({
    required this.stayType,
    required this.description,
    required this.facilities,
  });

  factory HotelRoomStay.fromJson(Map<String, dynamic> json) {
    final facilities = (json['roomStayFacilities'] as List? ?? [])
        .whereType<Map>()
        .map(
          (facility) => HotelRoomStayFacility.fromJson(
            Map<String, dynamic>.from(facility),
          ),
        )
        .toList();

    return HotelRoomStay(
      stayType: json['stayType']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      facilities: facilities,
    );
  }
}

class HotelRoomDetails {
  final String roomCode;
  final String roomType;
  final String characteristicCode;
  final int minPax;
  final int maxPax;
  final int maxAdults;
  final int maxChildren;
  final List<HotelRoomFacility> facilities;
  final List<HotelRoomStay> stays;
  final String pmsRoomCode;

  HotelRoomDetails({
    required this.roomCode,
    required this.roomType,
    required this.characteristicCode,
    required this.minPax,
    required this.maxPax,
    required this.maxAdults,
    required this.maxChildren,
    required this.facilities,
    required this.stays,
    required this.pmsRoomCode,
  });

  factory HotelRoomDetails.fromJson(Map<String, dynamic> json) {
    final facilities = (json['room_facilities'] as List? ?? [])
        .whereType<Map>()
        .map(
          (facility) =>
              HotelRoomFacility.fromJson(Map<String, dynamic>.from(facility)),
        )
        .toList();

    final stays = (json['room_stays'] as List? ?? [])
        .whereType<Map>()
        .map((stay) => HotelRoomStay.fromJson(Map<String, dynamic>.from(stay)))
        .toList();

    return HotelRoomDetails(
      roomCode: json['room_code']?.toString() ?? '',
      roomType: json['room_type']?.toString() ?? '',
      characteristicCode: json['characteristic_code']?.toString() ?? '',
      minPax: (json['min_pax'] as num?)?.toInt() ?? 0,
      maxPax: (json['max_pax'] as num?)?.toInt() ?? 0,
      maxAdults: (json['max_adults'] as num?)?.toInt() ?? 0,
      maxChildren: (json['max_children'] as num?)?.toInt() ?? 0,
      facilities: facilities,
      stays: stays,
      pmsRoomCode: json['pms_room_code']?.toString() ?? '',
    );
  }
}
