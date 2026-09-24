import 'package:flutter/material.dart';

import '../models/transport.dart';
import 'transfer_selection_page.dart';

class TransportDetailsPage extends StatefulWidget {
  final Map<String, dynamic> trip;
  final Transport transport;
  final bool hasSelectedHotel;

  const TransportDetailsPage({
    super.key,
    required this.trip,
    required this.transport,
    this.hasSelectedHotel = false,
  });

  @override
  State<TransportDetailsPage> createState() => _TransportDetailsPageState();
}

class _TransportDetailsPageState extends State<TransportDetailsPage> {
  bool _flightDetailsExpanded = true;

  Transport get transport => widget.transport;

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
    final isFirst = index == 0;
    final isLast = index == transport.segments.length - 1;

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

            if (segment.carrierCodeType != null &&
                segment.carrierCodeType!.isNotEmpty)
              Padding(padding: const EdgeInsets.only(top: 14)),

            if (!isFirst || !isLast) const SizedBox.shrink(),
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

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Your currency', style: TextStyle(fontSize: 14)),
                Text(
                  '${transport.userPrice.toStringAsFixed(2)} '
                  '${transport.userCurrency}',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),

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

            const SizedBox(height: 8),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Provider price', style: TextStyle(fontSize: 14)),
                Text(
                  '${transport.price.toStringAsFixed(2)} '
                  '${transport.currency}',
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
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: () {
              setState(() {
                _flightDetailsExpanded = !_flightDetailsExpanded;
              });
            },
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Trip details',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
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
          if (_flightDetailsExpanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
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
        ],
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

  void _onAddTransferPressed() {
    if (!canAddTransfer) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_addTransferHint())));
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TransferSelectionPage(
          trip: widget.trip,
          parentTransport: transport,
        ),
      ),
    );
  }

  Widget _buildAddTransferButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: _onAddTransferPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor:
              canAddTransfer ? Colors.blue : Colors.blue.shade200,
          foregroundColor: Colors.white,
        ),
        icon: const Icon(Icons.directions_car),
        label: const Text('Add transfer'),
      ),
    );
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
            // HEADER
            // =========================
            Row(
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
              ],
            ),

            const SizedBox(height: 24),

            // =========================
            // GENERAL DETAILS
            // =========================
            _buildGeneralDetails(),

            if (isFlight) ...[
              const SizedBox(height: 12),
              _buildAddTransferButton(),
            ],

            const SizedBox(height: 20),

            // =========================
            // FLIGHT SEGMENTS
            // =========================
            if (isFlight && transport.segments.isNotEmpty) ...[
              const Text(
                'Flight segments',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),

              const SizedBox(height: 12),

              ...transport.segments.asMap().entries.map(
                (entry) => _buildSegmentCard(entry.value, entry.key),
              ),

              if (transport.layovers.isNotEmpty) ...[
                const SizedBox(height: 8),

                const Text(
                  'Connections',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),

                const SizedBox(height: 12),

                ...transport.layovers.map(
                  (layover) => _buildLayoverCard(layover),
                ),
              ],
            ],

            const SizedBox(height: 8),

            // =========================
            // PRICE
            // =========================
            _buildPriceBlock(),

            const SizedBox(height: 20),

            // =========================
            // BOOKING
            // =========================
            _buildBookingButton(context),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
