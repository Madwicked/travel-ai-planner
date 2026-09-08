class Place {
  final int? id;
  final int? tripId;

  final String? externalId;
  final String source;

  final String name;
  final String city;
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
    return Place(
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      id: json['id'],
      tripId: json['trip_id'],
      externalId: json['external_id'],
      source: json['source'] ?? 'mock',
      name: json['name'],
      city: json['city'],
      category: json['category'],
      address: json['address'],
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      rating: (json['rating'] as num?)?.toDouble(),
      openingHours: json['opening_hours'] != null
          ? Map<String, dynamic>.from(json['opening_hours'])
          : null,
      openingTime: json['opening_time'],
      closingTime: json['closing_time'],
      visitDuration: json['visit_duration'],
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
