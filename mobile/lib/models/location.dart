class Location {
  final String name;
  final String country;
  final String countryCode;
  final double latitude;
  final double longitude;
  final String? iataCode;

  Location({
    required this.name,
    required this.country,
    required this.countryCode,
    required this.latitude,
    required this.longitude,
    this.iataCode,
  });

  factory Location.fromJson(Map<String, dynamic> json) {
    return Location(
      name: json['name'],
      country: json['country'],
      countryCode: json['country_code'],
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      iataCode: json['iata_code'],
    );
  }

  String get displayName => '$name, $country';
}