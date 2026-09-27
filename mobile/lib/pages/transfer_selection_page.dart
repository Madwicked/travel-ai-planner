import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'dart:convert';

import '../api_config.dart';
import '../models/hotel.dart';
import '../models/transport.dart';

class TransferSelectionPage extends StatefulWidget {
  final Map<String, dynamic> trip;
  final Transport parentTransport;
  final Hotel selectedHotel;

  const TransferSelectionPage({
    super.key,
    required this.trip,
    required this.parentTransport,
    required this.selectedHotel,
  });

  @override
  State<TransferSelectionPage> createState() => _TransferSelectionPageState();
}

class _TransferSelectionPageState extends State<TransferSelectionPage> {
  bool isLoading = true;
  String? errorMessage;

  List<Map<String, dynamic>> transferOptions = [];

  final Set<int> _expandedTransfers = {};
  final ScrollController _scrollController = ScrollController();
  bool _showScrollToTop = false;

  @override
  void initState() {
    super.initState();
    _loadTransferOptions();
  }

  Future<void> _loadTransferOptions() async {
    try {
      final isReturn = widget.parentTransport.direction == 'return';

      final airportLocation = isReturn
          ? widget.parentTransport.departureLocation
          : widget.parentTransport.arrivalLocation;

      final airportMatch = RegExp(r'\(([^)]+)\)$').firstMatch(airportLocation);

      final airportCode = airportMatch != null
          ? airportMatch.group(1)!.trim()
          : airportLocation.trim();

      const airportType = 'IATA';

      final hotelLatitude = widget.selectedHotel.latitude;
      final hotelLongitude = widget.selectedHotel.longitude;

      print('HOTEL NAME: ${widget.selectedHotel.name}');
      print('HOTEL LATITUDE: $hotelLatitude');
      print('HOTEL LONGITUDE: $hotelLongitude');
      print('TRANSFER AIRPORT: $airportCode');
      print('TRANSFER HOTEL: $hotelLatitude, $hotelLongitude');

      if (hotelLatitude == null || hotelLongitude == null) {
        throw Exception('Selected hotel coordinates are not available.');
      }

      final hotelCoordinates =
          '${hotelLatitude.toStringAsFixed(6)},'
          '${hotelLongitude.toStringAsFixed(6)}';

      final fromType = isReturn ? 'GPS' : airportType;
      final fromCode = isReturn ? hotelCoordinates : airportCode;

      final toType = isReturn ? airportType : 'GPS';
      final toCode = isReturn ? airportCode : hotelCoordinates;

      final date = isReturn
          ? widget.parentTransport.departureDate
          : widget.parentTransport.arrivalDate;

      final time = isReturn
          ? widget.parentTransport.departureTime
          : widget.parentTransport.arrivalTime;

      final outbound = '${date}T$time';

      final travelers = widget.trip['travelers'];

      final adults = travelers is int
          ? travelers
          : int.tryParse(travelers?.toString() ?? '') ?? 1;

      final uri = Uri.parse('${ApiConfig.baseUrl}/api/transfers/options')
          .replace(
            queryParameters: {
              'from_type': fromType,
              'from_code': fromCode,
              'to_type': toType,
              'to_code': toCode,
              'outbound': outbound,
              'adults': adults.toString(),
              'children': '0',
              'infants': '0',
              'language': 'en',
            },
          );

      final response = await http.get(uri);

      if (response.statusCode != 200) {
        throw Exception(
          'Server error: ${response.statusCode}\n${response.body}',
        );
      }

      final data = jsonDecode(response.body);

      final options = (data['options'] as List)
          .map((item) => Map<String, dynamic>.from(item))
          .toList();

      if (!mounted) return;

      setState(() {
        transferOptions = options;
        isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage = e.toString();
        isLoading = false;
      });
    }
  }

  void _selectTransfer(Map<String, dynamic> option) {
    Navigator.pop(context, {'type': 'transfer', 'option': option});
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Choose transfer',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: NotificationListener<ScrollNotification>(
        onNotification: (notification) {
          final shouldShow = _scrollController.offset > 500;

          if (shouldShow != _showScrollToTop) {
            setState(() {
              _showScrollToTop = shouldShow;
            });
          }

          return false;
        },
        child: _buildBody(),
      ),
      floatingActionButton: _showScrollToTop
          ? FloatingActionButton(
              onPressed: () {
                _scrollController.animateTo(
                  0,
                  duration: const Duration(milliseconds: 500),
                  curve: Curves.easeOut,
                );
              },
              child: const Icon(Icons.keyboard_arrow_up),
            )
          : null,
    );
  }

  Widget _buildBody() {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              const Text(
                'Failed to load transfer options.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                errorMessage!,
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey.shade600),
              ),
              const SizedBox(height: 20),
              OutlinedButton(
                onPressed: () {
                  setState(() {
                    isLoading = true;
                    errorMessage = null;
                  });

                  _loadTransferOptions();
                },
                child: const Text('Try again'),
              ),
            ],
          ),
        ),
      );
    }

    if (transferOptions.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'No transfer options were found.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 18),
          ),
        ),
      );
    }

    return ListView(
      controller: _scrollController,
      padding: const EdgeInsets.all(20),
      children: [
        const Text(
          'Choose a transfer',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Available transfer options for your selected hotel.',
          style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
        ),
        const SizedBox(height: 24),
        ...transferOptions.map(_buildTransferCard),
      ],
    );
  }

  Widget _buildTransferCard(Map<String, dynamic> option) {
    final index = transferOptions.indexOf(option);
    final isExpanded = _expandedTransfers.contains(index);

    final vehicleName = option['vehicle_name']?.toString() ?? 'Transfer';
    final categoryName = option['category_name']?.toString() ?? '';
    final transferType = option['transfer_type']?.toString() ?? '';

    final price = option['price'];
    final currency = option['currency']?.toString() ?? '';

    final cancellationPolicies = option['cancellation_policies'] is List
        ? List<Map<String, dynamic>>.from(
            (option['cancellation_policies'] as List).map(
              (item) => Map<String, dynamic>.from(item),
            ),
          )
        : <Map<String, dynamic>>[];

    final extras = option['extras'] is List
        ? List<Map<String, dynamic>>.from(
            (option['extras'] as List).map(
              (item) => Map<String, dynamic>.from(item),
            ),
          )
        : <Map<String, dynamic>>[];

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () {
          setState(() {
            if (isExpanded) {
              _expandedTransfers.remove(index);
            } else {
              _expandedTransfers.add(index);
            }
          });
        },
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.directions_car,
                      color: Colors.blue,
                      size: 30,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          vehicleName,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '$categoryName • $transferType',
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '$price $currency',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Icon(
                        isExpanded
                            ? Icons.keyboard_arrow_up
                            : Icons.keyboard_arrow_down,
                        color: Colors.grey,
                      ),
                    ],
                  ),
                ],
              ),

              if (isExpanded) ...[
                const SizedBox(height: 18),
                const Divider(),
                const SizedBox(height: 14),

                _buildSectionTitle('Transfer details'),

                const SizedBox(height: 10),

                _buildTransferDetail('Vehicle', vehicleName),

                _buildTransferDetail(
                  'Category',
                  categoryName.isNotEmpty ? categoryName : '—',
                ),

                _buildTransferDetail(
                  'Type',
                  transferType.isNotEmpty ? transferType : '—',
                ),

                _buildTransferDetail('Price', '$price $currency'),

                if (cancellationPolicies.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  _buildSectionTitle('Cancellation'),
                  const SizedBox(height: 8),
                  ...cancellationPolicies.map(_buildCancellationPolicy),
                ],

                if (extras.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  _buildSectionTitle('Available extras'),
                  const SizedBox(height: 8),
                  ...extras.map((extra) => _buildExtra(extra, currency)),
                ],

                const SizedBox(height: 18),

                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => _selectTransfer(option),
                    child: const Text('Select transfer'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildTransferDetail(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCancellationPolicy(Map<String, dynamic> policy) {
    final amount = policy['amount'];
    final currency = policy['currencyId']?.toString() ?? '';
    final from = policy['from']?.toString() ?? '';

    String formattedFrom = from;

    try {
      final dateTime = DateTime.parse(from);

      final day = dateTime.day.toString().padLeft(2, '0');
      final month = dateTime.month.toString().padLeft(2, '0');
      final year = dateTime.year;

      final hour = dateTime.hour.toString().padLeft(2, '0');
      final minute = dateTime.minute.toString().padLeft(2, '0');

      formattedFrom = '$day.$month.$year $hour:$minute';
    } catch (_) {
      // Keep original value if parsing fails.
    }

    final isFree = amount == 0 || amount == 0.0 || amount?.toString() == '0';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isFree ? Icons.check_circle_outline : Icons.info_outline,
            size: 20,
            color: isFree ? Colors.green : Colors.grey,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              isFree
                  ? 'Free cancellation until $formattedFrom'
                  : 'Cancellation fee: $amount $currency from $formattedFrom',
              style: const TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExtra(Map<String, dynamic> extra, String currency) {
    final type = extra['type']?.toString() ?? 'Extra';
    final amount = extra['amount'];

    final isFree = amount == 0 || amount == 0.0 || amount?.toString() == '0';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(
            isFree ? Icons.check_circle_outline : Icons.add_circle_outline,
            size: 20,
            color: isFree ? Colors.green : Colors.grey,
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(type, style: const TextStyle(fontSize: 14))),
          const SizedBox(width: 8),
          Text(
            isFree ? 'Free' : '+$amount $currency',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: isFree ? Colors.green : null,
            ),
          ),
        ],
      ),
    );
  }
}
