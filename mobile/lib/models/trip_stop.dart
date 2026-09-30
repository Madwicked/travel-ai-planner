class TripStop {
  final int id;
  final int tripId;
  final String city;
  final String? country;
  final double? latitude;
  final double? longitude;
  final DateTime startDate;
  final DateTime endDate;
  final int sortOrder;

  TripStop({
    required this.id,
    required this.tripId,
    required this.city,
    this.country,
    this.latitude,
    this.longitude,
    required this.startDate,
    required this.endDate,
    required this.sortOrder,
  });

  factory TripStop.fromJson(Map<String, dynamic> json) {
    return TripStop(
      id: (json['id'] as num).toInt(),
      tripId: (json['trip_id'] as num).toInt(),
      city: json['city']?.toString() ?? '',
      country: json['country']?.toString(),
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      startDate: DateTime.parse(json['start_date'].toString()),
      endDate: DateTime.parse(json['end_date'].toString()),
      sortOrder: (json['sort_order'] as num?)?.toInt() ?? 0,
    );
  }
}
