class HotelRate {
  final String roomName;
  final String boardCode;
  final String boardName;
  final String rateClass;
  final String rateType;
  final String paymentType;
  final double totalPrice;
  final double pricePerNight;
  final String currency;
  final int allotment;
  final int rooms;
  final int adults;
  final int children;
  final bool refundable;
  final List<dynamic> cancellationPolicies;
  final List<dynamic> taxes;
  final bool taxesIncluded;
  final double totalTaxes;

  HotelRate({
    required this.roomName,
    required this.boardCode,
    required this.boardName,
    required this.rateClass,
    required this.rateType,
    required this.paymentType,
    required this.totalPrice,
    required this.pricePerNight,
    required this.currency,
    required this.allotment,
    required this.rooms,
    required this.adults,
    required this.children,
    required this.refundable,
    required this.cancellationPolicies,
    required this.taxes,
    required this.taxesIncluded,
    required this.totalTaxes,
  });

  factory HotelRate.fromJson(Map<String, dynamic> json) {
    return HotelRate(
      roomName: json['room_name'] ?? 'Room',
      boardCode: json['board_code'] ?? '',
      boardName: json['board_name'] ?? '',
      rateClass: json['rate_class'] ?? '',
      rateType: json['rate_type'] ?? '',
      paymentType: json['payment_type'] ?? '',
      totalPrice: (json['total_price'] ?? 0).toDouble(),
      pricePerNight: (json['price_per_night'] ?? 0).toDouble(),
      currency: json['currency'] ?? 'EUR',
      allotment: json['allotment'] ?? 0,
      rooms: json['rooms'] ?? 0,
      adults: json['adults'] ?? 0,
      children: json['children'] ?? 0,
      refundable: json['refundable'] ?? false,
      cancellationPolicies: json['cancellation_policies'] ?? [],
      taxes: json['taxes'] ?? [],
      taxesIncluded: json['taxes_included'] ?? false,
      totalTaxes: (json['total_taxes'] ?? 0).toDouble(),
    );
  }
}

class Hotel {
  final int? id;
  final int? tripId;

  final String hotelCode;

  final String name;
  final String city;
  final String address;

  final String? description;
  final String? categoryCode;
  final String? categoryName;
  final String? accommodationType;

  final List<dynamic> facilities;

  final bool? petsAllowed;
  final bool? adultsOnly;

  final double? latitude;
  final double? longitude;

  final double pricePerNight;
  final int nights;
  final double totalPrice;
  final DateTime checkIn;
  final DateTime checkOut;
  final String currency;

  final double userPrice;
  final String userCurrency;
  final double destinationPrice;
  final String destinationCurrency;

  final List<HotelRate> rateOptions;

  Hotel({
    this.id,
    this.tripId,
    required this.hotelCode,
    required this.name,
    required this.city,
    required this.address,
    this.description,
    this.categoryCode,
    this.categoryName,
    this.accommodationType,
    required this.facilities,
    this.petsAllowed,
    this.adultsOnly,
    this.latitude,
    this.longitude,
    required this.pricePerNight,
    required this.nights,
    required this.totalPrice,
    required this.checkIn,
    required this.checkOut,
    required this.currency,
    required this.userPrice,
    required this.userCurrency,
    required this.destinationPrice,
    required this.destinationCurrency,
    required this.rateOptions,
  });

  factory Hotel.fromJson(Map<String, dynamic> json) {
    final rawRates = json['rate_options'] as List? ?? [];

    final rawFacilities = json['facilities'] as List? ?? [];

    return Hotel(
      id: json['id'],
      tripId: json['trip_id'],

      hotelCode: json['hotel_code']?.toString() ?? '',

      name: json['name']?.toString() ?? '',

      city: json['city']?.toString() ?? '',

      address: json['address']?.toString() ?? '',

      description: json['description']?.toString(),

      categoryCode: json['category_code']?.toString(),

      categoryName: json['category_name']?.toString(),

      accommodationType: json['accommodation_type']?.toString(),

      facilities: List<dynamic>.from(rawFacilities),

      petsAllowed: json['pets_allowed'] as bool?,

      adultsOnly: json['adults_only'] as bool?,

      latitude: json['latitude'] != null
          ? double.tryParse(json['latitude'].toString())
          : null,

      longitude: json['longitude'] != null
          ? double.tryParse(json['longitude'].toString())
          : null,

      pricePerNight: (json['price_per_night'] ?? 0).toDouble(),

      nights: json['nights'] ?? 0,

      totalPrice: (json['total_price'] ?? 0).toDouble(),

      checkIn: DateTime.parse(json['check_in']),

      checkOut: DateTime.parse(json['check_out']),

      currency: json['currency'] ?? 'EUR',

      userPrice: (json['user_price'] ?? 0).toDouble(),

      userCurrency: json['user_currency'] ?? 'EUR',

      destinationPrice: (json['destination_price'] ?? 0).toDouble(),

      destinationCurrency: json['destination_currency'] ?? 'EUR',

      rateOptions: rawRates
          .map((rate) => HotelRate.fromJson(rate as Map<String, dynamic>))
          .toList(),
    );
  }
  Hotel copyWith({
    double? pricePerNight,
    double? totalPrice,
    String? currency,
    double? userPrice,
    double? destinationPrice,
    List<HotelRate>? rateOptions,
  }) {
    return Hotel(
      id: id,
      tripId: tripId,
      hotelCode: hotelCode,
      name: name,
      city: city,
      address: address,
      description: description,
      categoryCode: categoryCode,
      categoryName: categoryName,
      accommodationType: accommodationType,
      facilities: facilities,
      petsAllowed: petsAllowed,
      adultsOnly: adultsOnly,
      latitude: latitude,
      longitude: longitude,
      pricePerNight: pricePerNight ?? this.pricePerNight,
      nights: nights,
      totalPrice: totalPrice ?? this.totalPrice,
      checkIn: checkIn,
      checkOut: checkOut,
      currency: currency ?? this.currency,
      userPrice: userPrice ?? this.userPrice,
      userCurrency: userCurrency,
      destinationPrice: destinationPrice ?? this.destinationPrice,
      destinationCurrency: destinationCurrency,
      rateOptions: rateOptions ?? this.rateOptions,
    );
  }
}
