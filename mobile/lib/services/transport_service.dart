import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api_config.dart';
import '../models/transport.dart';

class TransportService {
  static Future<List<Transport>> getTransportOptions({
    required int tripId,
    required bool isReturnTransport,
  }) async {
    final endpoint = isReturnTransport ? 'return-options' : 'options';

    final direction = isReturnTransport ? 'return' : 'outbound';

    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/transports/$endpoint',
    );

    final response = await http.get(url);

    if (response.statusCode != 200) {
      print('TRANSPORT OPTIONS STATUS: ${response.statusCode}');
      print('TRANSPORT OPTIONS BODY: ${response.body}');
      throw Exception('Server error: ${response.statusCode}');
    }

    print('TRANSPORT OPTIONS STATUS: ${response.statusCode}');
    print('TRANSPORT OPTIONS BODY: ${response.body}');

    final data = jsonDecode(response.body);

    return (data['options'] as List)
        .map(
          (transport) => Transport.fromJson({
            ...Map<String, dynamic>.from(transport),
            'direction': direction,
          }),
        )
        .toList();
  }

  static Future<List<Transport>> getTransports(int tripId) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/transports');

    final response = await http.get(url);

    if (response.statusCode != 200) {
      print('TRANSPORTS STATUS: ${response.statusCode}');
      print('TRANSPORTS BODY: ${response.body}');
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return (data['transports'] as List)
        .map(
          (transport) =>
              Transport.fromJson(Map<String, dynamic>.from(transport)),
        )
        .toList();
  }

  static Future<Transport> createTransport({
    required int tripId,
    required Transport transport,
  }) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/transports');

    final body = {
      'direction': transport.direction,

      'transport_type': transport.type,
      'transport_price': transport.price,
      'currency': transport.currency,
      'transport_duration': transport.duration,

      'departure_date': transport.departureDate,
      'departure_time': transport.departureTime,
      'departure_location': transport.departureLocation,

      'arrival_date': transport.arrivalDate,
      'arrival_time': transport.arrivalTime,
      'arrival_location': transport.arrivalLocation,
    };

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      print('CREATE TRANSPORT STATUS: ${response.statusCode}');
      print('CREATE TRANSPORT BODY: ${response.body}');
      throw Exception('Server error: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);

    return Transport.fromJson(Map<String, dynamic>.from(data['transport']));
  }

  static Future<void> deleteTransport({
    required int tripId,
    required int transportId,
  }) async {
    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/transports/$transportId',
    );

    final response = await http.delete(url);

    if (response.statusCode != 200) {
      print('STATUS: ${response.statusCode}');
      print('BODY: ${response.body}');
      throw Exception('Server error: ${response.statusCode}');
    }
  }
}
