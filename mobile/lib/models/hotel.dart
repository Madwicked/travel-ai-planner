class Hotel {
  final int? id;
  final int? tripId;
  final String name;
  final String city;
  final String address;
  final double pricePerNight;
  final int nights;
  final double totalPrice;
  final DateTime checkIn;
  final DateTime checkOut;

  const Hotel({
    this.id,
    this.tripId,
    required this.name,
    required this.city,
    required this.address,
    required this.pricePerNight,
    required this.nights,
    required this.totalPrice,
    required this.checkIn,
    required this.checkOut,
  });

  factory Hotel.fromJson(Map<String, dynamic> json) {
    return Hotel(
      id: json['id'],
      tripId: json['trip_id'],
      name: json['name'],
      city: json['city'],
      address: json['address'],
      pricePerNight:
          (json['price_per_night'] as num).toDouble(),
      nights: json['nights'],
      totalPrice:
          (json['total_price'] as num).toDouble(),
      checkIn: DateTime.parse(json['check_in']),
      checkOut: DateTime.parse(json['check_out']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'trip_id': tripId,
      'name': name,
      'city': city,
      'address': address,
      'price_per_night': pricePerNight,
      'nights': nights,
      'total_price': totalPrice,
      'check_in':
          checkIn.toIso8601String().split('T').first,
      'check_out':
          checkOut.toIso8601String().split('T').first,
    };
  }
}