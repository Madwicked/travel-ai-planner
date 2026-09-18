class Place {
  final int? id;
  final int? tripId;

  final String? externalId;
  final String source;

  final String name;
  final String city;
  final String? country;
  final String category;
  final String address;

  final double? latitude;
  final double? longitude;
  final double? rating;

  final Map<String, dynamic>? openingHours;

  final String openingTime;
  final String closingTime;

  final String? visitDuration;

  final double? distanceKm;

  const Place({
    this.distanceKm,
    this.id,
    this.tripId,
    this.externalId,
    required this.source,
    required this.name,
    required this.city,
    this.country,
    required this.category,
    required this.address,
    this.latitude,
    this.longitude,
    this.rating,
    this.openingHours,
    required this.openingTime,
    required this.closingTime,
    this.visitDuration,
  });

  factory Place.fromJson(Map<String, dynamic> json) {
    String? asString(dynamic value) {
      if (value == null) return null;
      return value.toString();
    }

    return Place(
      distanceKm: (json['distance_km'] as num?)?.toDouble(),

      id: json['id'] is num ? (json['id'] as num).toInt() : null,

      tripId: json['trip_id'] is num ? (json['trip_id'] as num).toInt() : null,

      externalId: asString(json['external_id']),

      source: asString(json['source']) ?? 'mock',

      name: asString(json['name']) ?? '',

      city: asString(json['city']) ?? '',

      country: asString(json['country']),

      category: asString(json['category']) ?? '',

      address: asString(json['address']) ?? '',

      latitude: (json['latitude'] as num?)?.toDouble(),

      longitude: (json['longitude'] as num?)?.toDouble(),

      rating: (json['rating'] as num?)?.toDouble(),

      openingHours: json['opening_hours'] != null
          ? Map<String, dynamic>.from(json['opening_hours'])
          : null,

      openingTime: asString(json['opening_time']) ?? '09:00',

      closingTime: asString(json['closing_time']) ?? '19:00',

      visitDuration: asString(json['visit_duration']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'distance_km': distanceKm,
      'id': id,
      'trip_id': tripId,
      'external_id': externalId,
      'source': source,
      'name': name,
      'city': city,
      'country': country,
      'category': category,
      'address': address,
      'latitude': latitude,
      'longitude': longitude,
      'rating': rating,
      'opening_hours': openingHours,
      'opening_time': openingTime,
      'closing_time': closingTime,
      'visit_duration': visitDuration,
    };
  }
}
