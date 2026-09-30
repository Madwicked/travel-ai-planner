import 'package:flutter/material.dart';

import '../models/transport.dart';
import '../services/transport_service.dart';
import '../models/hotel.dart';

class TransportDetailsPage extends StatefulWidget {
  final Map<String, dynamic> trip;
  final Transport transport;
  final bool hasSelectedHotel;
  final Hotel? selectedHotel;
  final Future<void> Function()? onAddTransfer;

  const TransportDetailsPage({
    super.key,
    required this.trip,
    required this.transport,
    this.hasSelectedHotel = false,
    this.selectedHotel,
    this.onAddTransfer,
  });

  @override
  State<TransportDetailsPage> createState() => _TransportDetailsPageState();
}

class _TransportDetailsPageState extends State<TransportDetailsPage> {
  bool _flightDetailsExpanded = false;
  bool _transferExpanded = false;
  bool _transferLoading = true;
  Transport? _selectedTransfer;

  Transport get transport => widget.transport;

  @override
  void initState() {
    super.initState();
    _loadSelectedTransfer();
  }

  Future<void> _loadSelectedTransfer() async {
    try {
      final transports = await TransportService.getTransports(
        widget.trip['id'],
      );

      if (!mounted) return;

      Transport? selectedTransfer;

      if (transport.id != null) {
        for (final item in transports) {
          if (!item.type.startsWith('Transfer')) {
            continue;
          }

          if (item.parentTransportId == transport.id) {
            selectedTransfer = item;
            break;
          }
        }
      }

      setState(() {
        _selectedTransfer = selectedTransfer;
        _transferLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _transferLoading = false;
      });
    }
  }

  bool get hasSelectedTicket => transport.id != null;

  bool get canAddTransfer => hasSelectedTicket && widget.hasSelectedHotel;

  IconData getTransportIcon(String type) {
    if (type.startsWith('Flight')) {
      return Icons.flight;
    }

    if (type.startsWith('Bus')) {
      return Icons.directions_bus;
    }

    if (type.startsWith('Train')) {
      return Icons.train;
    }

    if (type.startsWith('Transfer')) {
      return Icons.directions_car;
    }

    return Icons.directions_transit;
  }

  String _formatSegmentTitle(TransportSegment segment) {
    final carrier = segment.carrier?.trim();
    final carrierCode = segment.carrierCode?.trim();
    final flightNumber = segment.flightNumber?.trim();

    if (carrierCode != null &&
        carrierCode.isNotEmpty &&
        flightNumber != null &&
        flightNumber.isNotEmpty) {
      if (carrier != null && carrier.isNotEmpty) {
        return '$carrier · $carrierCode $flightNumber';
      }

      return '$carrierCode $flightNumber';
    }

    if (carrier != null && carrier.isNotEmpty) {
      if (flightNumber != null && flightNumber.isNotEmpty) {
        return '$carrier · $flightNumber';
      }

      return carrier;
    }

    if (flightNumber != null && flightNumber.isNotEmpty) {
      return flightNumber;
    }

    return 'Flight segment';
  }

  String _formatAirport(String location) {
    return location;
  }

  Widget _buildInfoRow(String title, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 105,
            child: Text(
              title,
              style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRoutePoint({
    required String location,
    required String date,
    required String time,
    required bool isDeparture,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 12,
          height: 12,
          margin: const EdgeInsets.only(top: 5),
          decoration: BoxDecoration(
            color: isDeparture ? Colors.blue : Colors.green,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                time,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                date,
                style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 4),
              Text(
                _formatAirport(location),
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSegmentCard(TransportSegment segment, int index) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.flight, color: Colors.blue, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _formatSegmentTitle(segment),
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 18),

            _buildRoutePoint(
              location: segment.departureLocation,
              date: segment.departureDate,
              time: segment.departureTime,
              isDeparture: true,
            ),

            Padding(
              padding: const EdgeInsets.only(left: 5, top: 4, bottom: 4),
              child: Row(
                children: [
                  Container(width: 2, height: 28, color: Colors.grey.shade300),
                  const SizedBox(width: 17),
                  Text(
                    segment.duration,
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),

            _buildRoutePoint(
              location: segment.arrivalLocation,
              date: segment.arrivalDate,
              time: segment.arrivalTime,
              isDeparture: false,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLayoverCard(Map<String, dynamic> layover) {
    final location = layover['location']?.toString() ?? '';
    final duration = layover['duration']?.toString() ?? '';

    return Container(
      margin: const EdgeInsets.only(left: 16, right: 16, bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.orange.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.orange.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          const Icon(Icons.access_time, color: Colors.orange, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Connection',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 2),
                Text(location, style: const TextStyle(fontSize: 14)),
              ],
            ),
          ),
          Text(
            duration,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceBlock() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Price',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            const SizedBox(height: 8),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Destination currency',
                  style: TextStyle(fontSize: 14),
                ),
                Text(
                  '${transport.destinationPrice.toStringAsFixed(2)} '
                  '${transport.destinationCurrency}',
                  style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGeneralDetails() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Trip details',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            _buildInfoRow('Transport', transport.type),
            _buildInfoRow('Total duration', transport.duration),
            _buildInfoRow('Stops', transport.stops.toString()),

            _buildInfoRow(
              'Departure',
              '${transport.departureDate} '
                  '${transport.departureTime}',
            ),

            _buildInfoRow(
              'Arrival',
              '${transport.arrivalDate} '
                  '${transport.arrivalTime}',
            ),

            _buildInfoRow('From', transport.departureLocation),

            _buildInfoRow('To', transport.arrivalLocation),
          ],
        ),
      ),
    );
  }

  String _addTransferHint() {
    if (!hasSelectedTicket && !widget.hasSelectedHotel) {
      return 'Select a ticket and a hotel to add a transfer.';
    }

    if (!hasSelectedTicket) {
      return 'Select a ticket to add a transfer.';
    }

    return 'Select a hotel to add a transfer.';
  }

  Future<void> _onAddTransferPressed() async {
    if (!canAddTransfer) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(_addTransferHint())));
      return;
    }

    if (widget.onAddTransfer == null) {
      return;
    }

    try {
      await widget.onAddTransfer!();

      if (!mounted) return;

      await _loadSelectedTransfer();
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to add transfer: $e')));
    }
  }

  Future<void> _deleteTransfer() async {
    final transfer = _selectedTransfer;

    if (transfer == null || transfer.id == null) {
      return;
    }

    try {
      await TransportService.deleteTransport(
        tripId: widget.trip['id'],
        transportId: transfer.id!,
      );

      if (!mounted) return;

      setState(() {
        _selectedTransfer = null;
        _transferExpanded = false;
      });

      Navigator.pop(context, true);
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to delete transfer: $e')));
    }
  }

  Widget _buildTransferCard() {
    if (_transferLoading) {
      return Card(
        margin: const EdgeInsets.only(bottom: 12),
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: const Padding(
          padding: EdgeInsets.all(18),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    final transfer = _selectedTransfer;

    if (transfer == null) {
      return Card(
        margin: const EdgeInsets.only(bottom: 12),
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.directions_car,
                      color: Colors.blue,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Text(
                      'Transfer',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                'No transfer selected',
                style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _onAddTransferPressed,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: canAddTransfer
                        ? Colors.blue
                        : Colors.blue.shade200,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Add transfer'),
                ),
              ),
            ],
          ),
        ),
      );
    }

    final data = transfer.transferData ?? {};

    final vehicleName =
        data['vehicle_name']?.toString().trim().isNotEmpty == true
        ? data['vehicle_name'].toString()
        : 'Transfer';

    final categoryName =
        data['category_name']?.toString().trim().isNotEmpty == true
        ? data['category_name'].toString()
        : '';

    final transferType =
        data['transfer_type']?.toString().trim().isNotEmpty == true
        ? data['transfer_type'].toString()
        : '';

    final extras = data['extras'] is List
        ? List<Map<String, dynamic>>.from(
            (data['extras'] as List).map(
              (item) => Map<String, dynamic>.from(item),
            ),
          )
        : <Map<String, dynamic>>[];

    final cancellationPolicies = data['cancellation_policies'] is List
        ? List<Map<String, dynamic>>.from(
            (data['cancellation_policies'] as List).map(
              (item) => Map<String, dynamic>.from(item),
            ),
          )
        : <Map<String, dynamic>>[];

    final String title = transfer.direction == 'return'
        ? 'Hotel → Airport'
        : 'Airport → Hotel';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Stack(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                InkWell(
                  onTap: () {
                    setState(() {
                      _transferExpanded = !_transferExpanded;
                    });
                  },
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: Colors.blue.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.directions_car,
                              color: Colors.blue,
                              size: 24,
                            ),
                          ),
                          const SizedBox(width: 12),
                          const Expanded(
                            child: Text(
                              'Transfer',
                              style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                '${transfer.userPrice} '
                                '${transfer.userCurrency}',
                                style: const TextStyle(
                                  fontSize: 17,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${transfer.destinationPrice} '
                                '${transfer.destinationCurrency}',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey.shade500,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(width: 6),
                          Icon(
                            _transferExpanded
                                ? Icons.keyboard_arrow_up
                                : Icons.keyboard_arrow_down,
                            color: Colors.grey.shade700,
                          ),
                        ],
                      ),

                      const SizedBox(height: 14),

                      Text(
                        title,
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey.shade600,
                        ),
                      ),

                      const SizedBox(height: 6),

                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.location_on_outlined, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              transfer.departureLocation,
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),

                      const Padding(
                        padding: EdgeInsets.only(left: 9),
                        child: SizedBox(
                          height: 18,
                          child: VerticalDivider(width: 1, thickness: 1),
                        ),
                      ),

                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.location_on, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              transfer.arrivalLocation,
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 12),

                      Row(
                        children: [
                          Icon(
                            Icons.calendar_today_outlined,
                            size: 16,
                            color: Colors.grey.shade600,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            transfer.departureDate,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey.shade600,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Icon(
                            Icons.access_time,
                            size: 16,
                            color: Colors.grey.shade600,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            transfer.departureTime,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 12),

                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              transfer.type,
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                if (_transferExpanded) ...[
                  const Divider(),
                  const SizedBox(height: 14),

                  const Text(
                    'Selected transfer',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),

                  const SizedBox(height: 10),

                  _buildInfoRow('Vehicle', vehicleName),

                  _buildInfoRow(
                    'Category',
                    categoryName.isNotEmpty ? categoryName : '—',
                  ),

                  _buildInfoRow(
                    'Type',
                    transferType.isNotEmpty ? transferType : '—',
                  ),

                  _buildInfoRow('From', transfer.departureLocation),

                  _buildInfoRow('To', transfer.arrivalLocation),

                  _buildInfoRow('Date', transfer.departureDate),

                  _buildInfoRow('Time', transfer.departureTime),

                  _buildInfoRow(
                    'Price',
                    '${transfer.userPrice.toStringAsFixed(2)} '
                        '${transfer.userCurrency}',
                  ),

                  if (extras.isNotEmpty) ...[
                    const SizedBox(height: 12),

                    const Text(
                      'Available extras',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),

                    const SizedBox(height: 8),

                    ...extras.map(_buildTransferExtra),
                  ],

                  if (cancellationPolicies.isNotEmpty) ...[
                    const SizedBox(height: 12),

                    const Text(
                      'Cancellation',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),

                    const SizedBox(height: 8),

                    ...cancellationPolicies.map(_buildTransferCancellation),
                  ],
                ],
              ],
            ),

            Positioned(
              right: 0,
              bottom: 0,
              child: IconButton(
                onPressed: _deleteTransfer,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                icon: const Icon(
                  Icons.delete_outline,
                  color: Colors.red,
                  size: 24, // ← РАЗМЕР ИКОНКИ КОРЗИНЫ
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTransferExtra(Map<String, dynamic> extra) {
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
          if (!isFree)
            Text(
              '+$amount',
              style: const TextStyle(fontWeight: FontWeight.w600),
            )
          else
            const Text(
              'Free',
              style: TextStyle(
                color: Colors.green,
                fontWeight: FontWeight.w600,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildTransferCancellation(Map<String, dynamic> policy) {
    final amount = policy['amount'];
    final currency = policy['currencyId']?.toString() ?? '';
    final from = policy['from']?.toString() ?? '';

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
                  ? 'Free cancellation until $from'
                  : 'Cancellation fee: $amount $currency from $from',
              style: const TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _deleteTransport() async {
    if (transport.id == null) {
      return;
    }

    try {
      await TransportService.deleteTransport(
        tripId: widget.trip['id'],
        transportId: transport.id!,
      );

      if (!mounted) return;

      Navigator.pop(context, true);
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to delete transport: $e')));
    }
  }

  Widget _buildBookingButton(BuildContext context) {
    if (transport.bookingUrl == null || transport.bookingUrl!.isEmpty) {
      return const SizedBox.shrink();
    }

    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Booking link is available for this flight.'),
            ),
          );
        },
        icon: const Icon(Icons.open_in_new),
        label: const Text('Book this flight'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool isFlight = transport.type.startsWith('Flight');

    return Scaffold(
      appBar: AppBar(
        title: Text(
          isFlight ? 'Flight Details' : 'Transport Details',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // =========================
            // FLIGHT CARD
            // =========================
            Card(
              elevation: 1,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  InkWell(
                    onTap: isFlight
                        ? () {
                            setState(() {
                              _flightDetailsExpanded = !_flightDetailsExpanded;
                            });
                          }
                        : null,
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.blue.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Icon(
                              getTransportIcon(transport.type),
                              color: Colors.blue,
                              size: 32,
                            ),
                          ),

                          const SizedBox(width: 14),

                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  transport.type,
                                  style: const TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),

                                const SizedBox(height: 6),

                                Text(
                                  transport.duration,
                                  style: TextStyle(
                                    fontSize: 15,
                                    color: Colors.grey.shade600,
                                  ),
                                ),

                                if (isFlight) const SizedBox(height: 4),

                                if (isFlight)
                                  Text(
                                    transport.stops == 0
                                        ? 'Direct flight'
                                        : '${transport.stops} '
                                              '${transport.stops == 1 ? 'stop' : 'stops'}',
                                    style: TextStyle(
                                      fontSize: 14,
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                              ],
                            ),
                          ),

                          if (isFlight)
                            Icon(
                              _flightDetailsExpanded
                                  ? Icons.expand_less
                                  : Icons.expand_more,
                              color: Colors.grey.shade700,
                            ),
                        ],
                      ),
                    ),
                  ),

                  if (!isFlight || _flightDetailsExpanded)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
                      child: Column(
                        children: [
                          _buildGeneralDetails(),

                          const SizedBox(height: 20),

                          if (isFlight && transport.segments.isNotEmpty) ...[
                            const Align(
                              alignment: Alignment.centerLeft,
                              child: Text(
                                'Flight segments',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),

                            const SizedBox(height: 12),

                            ...transport.segments.asMap().entries.map(
                              (entry) =>
                                  _buildSegmentCard(entry.value, entry.key),
                            ),

                            if (transport.layovers.isNotEmpty) ...[
                              const SizedBox(height: 8),

                              const Align(
                                alignment: Alignment.centerLeft,
                                child: Text(
                                  'Connections',
                                  style: TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),

                              const SizedBox(height: 12),

                              ...transport.layovers.map(
                                (layover) => _buildLayoverCard(layover),
                              ),
                            ],
                          ],

                          const SizedBox(height: 8),

                          _buildPriceBlock(),

                          const SizedBox(height: 20),

                          _buildBookingButton(context),

                          const SizedBox(height: 12),

                          SizedBox(
                            width: double.infinity,
                            child: OutlinedButton.icon(
                              onPressed: _deleteTransport,
                              icon: const Icon(
                                Icons.delete_outline,
                                color: Colors.red,
                              ),
                              label: Text(
                                isFlight ? 'Delete flight' : 'Delete transport',
                                style: const TextStyle(color: Colors.red),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),

            if (isFlight) ...[const SizedBox(height: 20), _buildTransferCard()],

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
