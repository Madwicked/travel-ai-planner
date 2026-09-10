class Transport {
  final int? id;
  final int? tripId;

  final String direction;
  final String type;

  final double price;
  final String currency;

  final double destinationPrice;
  final String destinationCurrency;

  final double userPrice;
  final String userCurrency;

  final String duration;

  final String departureDate;
  final String departureTime;
  final String departureLocation;

  final String arrivalDate;
  final String arrivalTime;
  final String arrivalLocation;

  final String? bookingUrl;

  const Transport({
    this.id,
    this.tripId,
    required this.direction,
    required this.type,
    required this.price,
    required this.currency,
    required this.destinationPrice,
    required this.destinationCurrency,
    required this.userPrice,
    required this.userCurrency,
    required this.duration,
    required this.departureDate,
    required this.departureTime,
    required this.departureLocation,
    required this.arrivalDate,
    required this.arrivalTime,
    required this.arrivalLocation,
    this.bookingUrl,
  });

  factory Transport.fromJson(Map<String, dynamic> json) {
    return Transport(
      id: json['id'],
      tripId: json['trip_id'],
      direction: json['direction'] ?? '',
      type: json['type'] ?? '',
      price: (json['price'] as num).toDouble(),
      currency: json['currency'] ?? 'EUR',

      destinationPrice: (json['destination_price'] as num).toDouble(),
      destinationCurrency: json['destination_currency'] ?? 'EUR',

      userPrice: (json['user_price'] as num).toDouble(),
      userCurrency: json['user_currency'] ?? 'EUR',

      duration: json['duration'] ?? '',
      departureDate: json['departure_date'] ?? '',
      departureTime: json['departure_time'] ?? '',
      departureLocation: json['departure_location'] ?? '',
      arrivalDate: json['arrival_date'] ?? '',
      arrivalTime: json['arrival_time'] ?? '',
      arrivalLocation: json['arrival_location'] ?? '',
      bookingUrl: json['booking_url'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'trip_id': tripId,
      'direction': direction,
      'type': type,
      'price': price,
      'currency': currency,

      'destination_price': destinationPrice,
      'destination_currency': destinationCurrency,

      'user_price': userPrice,
      'user_currency': userCurrency,

      'duration': duration,
      'departure_date': departureDate,
      'departure_time': departureTime,
      'departure_location': departureLocation,
      'arrival_date': arrivalDate,
      'arrival_time': arrivalTime,
      'arrival_location': arrivalLocation,
      'booking_url': bookingUrl,
    };
  }
}
