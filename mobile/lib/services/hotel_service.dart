import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api_config.dart';
import '../models/hotel.dart';
import '../models/hotel_room.dart';

class HotelService {
  static Future<List<Hotel>> getHotelOptions(int tripId, {int? stopId}) async {
    var url = '${ApiConfig.baseUrl}/api/trips/$tripId/hotels/options';

    if (stopId != null) {
      url += '?stop_id=$stopId';
    }

    final response = await http.get(Uri.parse(url));

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return (data['options'] as List)
        .map((hotel) => Hotel.fromJson(Map<String, dynamic>.from(hotel)))
        .toList();
  }

  static Future<Hotel> createHotel({
    required int tripId,
    required Hotel hotel,
    int? stopId,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/hotels');

    final body = {
      'name': hotel.name,
      'city': hotel.city,
      'address': hotel.address,
      'price_per_night': hotel.pricePerNight,
      'nights': hotel.nights,
      'total_price': hotel.totalPrice,
      'currency': hotel.currency,
      'check_in': hotel.checkIn.toIso8601String().split('T').first,
      'check_out': hotel.checkOut.toIso8601String().split('T').first,
      'latitude': hotel.latitude,
      'longitude': hotel.longitude,
      'stop_id': stopId,
      'hotel_data': {
        'hotel_code': hotel.hotelCode,
        'room_code': hotel.rateOptions.isNotEmpty
            ? hotel.rateOptions.first.roomCode
            : null,
        'description': hotel.description,
        'category_code': hotel.categoryCode,
        'category_name': hotel.categoryName,
        'accommodation_type': hotel.accommodationType,
        'facilities': hotel.facilities,
        'pets_allowed': hotel.petsAllowed,
        'adults_only': hotel.adultsOnly,
        'rate_options': hotel.rateOptions
            .map(
              (rate) => {
                'room_name': rate.roomName,
                'room_code': rate.roomCode,
                'board_code': rate.boardCode,
                'board_name': rate.boardName,
                'rate_class': rate.rateClass,
                'rate_type': rate.rateType,
                'payment_type': rate.paymentType,
                'total_price': rate.totalPrice,
                'price_per_night': rate.pricePerNight,
                'currency': rate.currency,
                'allotment': rate.allotment,
                'rooms': rate.rooms,
                'adults': rate.adults,
                'children': rate.children,
                'refundable': rate.refundable,
                'cancellation_policies': rate.cancellationPolicies,
                'taxes': rate.taxes,
                'taxes_included': rate.taxesIncluded,
                'total_taxes': rate.totalTaxes,
              },
            )
            .toList(),
      },
    };

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return Hotel.fromJson(Map<String, dynamic>.from(data['hotel']));
  }

  static Future<List<Hotel>> getHotels(int tripId) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/hotels');

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return (data['hotels'] as List)
        .map((hotel) => Hotel.fromJson(Map<String, dynamic>.from(hotel)))
        .toList();
  }

  static Future<HotelRoomDetails> getHotelRoomDetails({
    required int tripId,
    required int hotelId,
    required String roomCode,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/'
      '$tripId/hotels/$hotelId/rooms/'
      '$roomCode',
    );

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception(
        'Server error: ${response.statusCode}, body: ${response.body}',
      );
    }

    final data = jsonDecode(response.body);

    return HotelRoomDetails.fromJson(Map<String, dynamic>.from(data));
  }

  static Future<Map<String, dynamic>> deleteHotel({
    required int tripId,
    required int hotelId,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/hotels/$hotelId',
    );

    final response = await http.delete(url);

    if (response.statusCode != 200) {
      throw Exception('Server error: ${response.statusCode}');
    }

    return Map<String, dynamic>.from(jsonDecode(response.body));
  }
}
