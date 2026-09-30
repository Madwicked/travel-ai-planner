import 'package:flutter/material.dart';

import '../models/trip_stop.dart';

import 'hotel_rates_page.dart';
import 'hotel_options_page.dart';
import '../models/hotel.dart';
import '../models/hotel_room.dart';
import '../services/hotel_service.dart';
import '../widgets/location_map.dart';

class HotelDetailsPage extends StatefulWidget {
  final Hotel hotel;
  final Map<String, dynamic> trip;
  final TripStop? stop;
  final TripStop? nextStop;

  const HotelDetailsPage({
    super.key,
    required this.hotel,
    required this.trip,
    this.stop,
    this.nextStop,
  });

  @override
  State<HotelDetailsPage> createState() => _HotelDetailsPageState();
}

class _HotelDetailsPageState extends State<HotelDetailsPage> {
  bool isDeleting = false;
  HotelRoomDetails? roomDetails;
  bool isLoadingRoomDetails = false;
  String? roomDetailsError;

  Hotel? _currentHotel;

  Hotel get hotel => _currentHotel ?? widget.hotel;

  Map<String, dynamic> get trip => widget.trip;

  String _formatPaymentType(String value) {
    switch (value.toLowerCase()) {
      case 'at_web':
        return 'Pay on website';
      case 'at_hotel':
        return 'Pay at hotel';
      case 'pay_now':
        return 'Pay now';
      case 'pay_later':
        return 'Pay later';
      default:
        return value;
    }
  }

  Widget _buildInfoRow(String title, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(
              title,
              style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceRow(String title, String value, {bool primary = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(child: Text(title, style: const TextStyle(fontSize: 14))),
        const SizedBox(width: 16),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.right,
            style: primary
                ? const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)
                : TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
        ),
      ],
    );
  }

  String _formatDate(DateTime? date) {
    if (date == null) {
      return '-';
    }

    return '${date.day.toString().padLeft(2, '0')}.'
        '${date.month.toString().padLeft(2, '0')}.'
        '${date.year}';
  }

  Future<void> _loadRoomDetails() async {
    print('=== LOAD ROOM DETAILS START ===');

    final hotelId = hotel.id;
    final tripId = trip['id'] is num ? (trip['id'] as num).toInt() : null;

    print('hotelId: $hotelId');
    print('hotel.tripId: $tripId');
    print('trip from page: $trip');
    print('rateOptions count: ${hotel.rateOptions.length}');

    if (hotelId == null || tripId == null) {
      print('ROOM DETAILS STOP: hotelId or tripId is null');
      return;
    }

    if (hotel.rateOptions.isEmpty) {
      return;
    }

    final roomCode = hotel.rateOptions.first.roomCode;

    print('roomCode: $roomCode');

    if (roomCode.isEmpty) {
      print('ROOM DETAILS STOP: roomCode is empty');
      return;
    }

    setState(() {
      isLoadingRoomDetails = true;
      roomDetailsError = null;
    });

    try {
      print('ROOM DETAILS REQUEST:');
      print('tripId: $tripId');
      print('hotelId: $hotelId');
      print('roomCode: $roomCode');

      final details = await HotelService.getHotelRoomDetails(
        tripId: tripId,
        hotelId: hotelId,
        roomCode: roomCode,
      );

      print('ROOM DETAILS LOADED');
      print('room type: ${details.roomType}');
      print('facilities: ${details.facilities.length}');
      print('stays: ${details.stays.length}');

      if (!mounted) {
        return;
      }

      setState(() {
        roomDetails = details;
        isLoadingRoomDetails = false;
      });
    } catch (e) {
      print('ROOM DETAILS ERROR: $e');

      if (!mounted) {
        return;
      }

      setState(() {
        isLoadingRoomDetails = false;
        roomDetailsError = e.toString();
      });
    }
  }

  Widget _buildStayCard() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Stay',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _buildInfoRow('Check-in', _formatDate(hotel.checkIn)),
            _buildInfoRow('Check-out', _formatDate(hotel.checkOut)),
            _buildInfoRow('Nights', hotel.nights.toString()),
          ],
        ),
      ),
    );
  }

  Widget _buildRoomDetailsCard() {
    if (isLoadingRoomDetails) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(18),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    if (roomDetailsError != null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Text(
            'Failed to load room details',
            style: TextStyle(color: Colors.grey.shade700),
          ),
        ),
      );
    }

    final room = roomDetails;

    if (room == null) {
      return const SizedBox.shrink();
    }

    final roomFacilities = room.facilities
        .where((facility) => facility.description.isNotEmpty)
        .toList();

    final stayFacilities = room.stays
        .expand((stay) => stay.facilities)
        .where((facility) => facility.description.isNotEmpty)
        .toList();

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Room details',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            _buildInfoRow('Room type', room.roomType),

            _buildInfoRow('Capacity', '${room.minPax}-${room.maxPax} guests'),

            _buildInfoRow('Adults', 'up to ${room.maxAdults}'),

            if (room.maxChildren > 0)
              _buildInfoRow('Children', 'up to ${room.maxChildren}'),

            if (roomFacilities.isNotEmpty) ...[
              const SizedBox(height: 14),

              const Text(
                'Facilities',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),

              const SizedBox(height: 8),

              ...roomFacilities.map((facility) {
                final value = facility.number != null
                    ? '${facility.description}: '
                          '${facility.number}'
                    : facility.description;

                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.check_circle_outline, size: 19),
                      const SizedBox(width: 10),
                      Expanded(child: Text(value)),
                    ],
                  ),
                );
              }),
            ],

            if (stayFacilities.isNotEmpty) ...[
              const SizedBox(height: 14),

              const Text(
                'Bed',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),

              const SizedBox(height: 8),

              ...stayFacilities.map((facility) {
                final value = facility.number != null
                    ? '${facility.description}: '
                          '${facility.number}'
                    : facility.description;

                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.bed, size: 19),
                      const SizedBox(width: 10),
                      Expanded(child: Text(value)),
                    ],
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildFacilitiesCard() {
    if (hotel.facilities.isEmpty) {
      return const SizedBox.shrink();
    }

    final facilities = hotel.facilities
        .map((facility) {
          if (facility is String) {
            return facility;
          }

          if (facility is Map) {
            return facility['name']?.toString() ??
                facility['description']?.toString() ??
                facility['code']?.toString() ??
                '';
          }

          return facility.toString();
        })
        .where((facility) => facility.isNotEmpty)
        .toList();

    if (facilities.isEmpty) {
      return const SizedBox.shrink();
    }

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Facilities',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            ...facilities.map(
              (facility) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 5),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.check_circle_outline,
                      size: 20,
                      color: Colors.blue,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        facility,
                        style: const TextStyle(fontSize: 14),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSelectedRateCard() {
    if (hotel.rateOptions.isEmpty) {
      return const SizedBox.shrink();
    }

    final selectedRate = hotel.rateOptions.first;

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Selected option',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _buildInfoRow('Room', selectedRate.roomName),
            if (selectedRate.boardName.isNotEmpty)
              _buildInfoRow('Meal plan', selectedRate.boardName),
            _buildInfoRow('Refundable', selectedRate.refundable ? 'Yes' : 'No'),
            _buildInfoRow(
              'Payment',
              _formatPaymentType(selectedRate.paymentType),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPriceCard() {
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
            _buildPriceRow(
              'Your currency',
              '${hotel.userPrice.toStringAsFixed(2)} '
                  '${hotel.userCurrency}',
              primary: true,
            ),
            const SizedBox(height: 8),
            _buildPriceRow(
              'Destination currency',
              '${hotel.destinationPrice.toStringAsFixed(2)} '
                  '${hotel.destinationCurrency}',
            ),
            const SizedBox(height: 8),
            _buildPriceRow(
              'Price per night',
              '${hotel.pricePerNight.toStringAsFixed(2)} '
                  '${hotel.currency}',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIntercityTransferCard() {
    final currentStop = widget.stop;
    final nextStop = widget.nextStop;

    if (currentStop == null || nextStop == null) {
      return const SizedBox.shrink();
    }

    final hasIntercityTransfer =
        currentStop.city.trim().toLowerCase() !=
        nextStop.city.trim().toLowerCase();

    if (!hasIntercityTransfer) {
      return const SizedBox.shrink();
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
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
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 14),

            Text(
              'Hotel → Hotel',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),

            const SizedBox(height: 6),

            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.location_on_outlined, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    currentStop.city,
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
                    nextStop.city,
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
                  _formatDate(currentStop.endDate),
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                ),
              ],
            ),

            const SizedBox(height: 12),

            Text(
              'Intercity transfer',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _changeHotel() async {
    final result = await Navigator.push<Hotel>(
      context,
      MaterialPageRoute(
        builder: (_) => HotelOptionsPage(trip: trip, stop: widget.stop),
      ),
    );

    if (result == null || !mounted) {
      return;
    }

    Navigator.pop(context, result);
  }

  Future<void> _changeRoom() async {
    if (hotel.rateOptions.isEmpty) {
      return;
    }

    final selectedRate = await Navigator.push<HotelRate>(
      context,
      MaterialPageRoute(builder: (_) => HotelRatesPage(hotel: hotel)),
    );

    if (selectedRate == null || !mounted) {
      return;
    }

    final updatedRates = [
      selectedRate,
      ...hotel.rateOptions.where((rate) => rate != selectedRate),
    ];

    final updatedHotel = hotel.copyWith(
      pricePerNight: selectedRate.pricePerNight,
      totalPrice: selectedRate.totalPrice,
      currency: selectedRate.currency,
      rateOptions: updatedRates,
    );

    try {
      final savedHotel = await HotelService.createHotel(
        tripId: trip['id'],
        hotel: updatedHotel,
        stopId: widget.stop?.id,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _currentHotel = savedHotel;
      });

      await _loadRoomDetails();
    } catch (e) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to update room: $e')));
    }
  }

  Future<void> _deleteHotel() async {
    if (hotel.id == null || hotel.tripId == null) {
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Delete hotel?'),
          content: const Text(
            'Are you sure you want to remove this hotel from the trip?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Delete', style: TextStyle(color: Colors.red)),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) {
      return;
    }

    setState(() {
      isDeleting = true;
    });

    try {
      await HotelService.deleteHotel(tripId: hotel.tripId!, hotelId: hotel.id!);

      if (!mounted) return;

      Navigator.pop(context, true);
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isDeleting = false;
      });

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to delete hotel: $e')));
    }
  }

  @override
  void initState() {
    super.initState();

    _currentHotel = widget.hotel;

    _loadRoomDetails();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Hotel Details',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.blue.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(Icons.hotel, color: Colors.blue, size: 32),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        hotel.name,
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        hotel.city,
                        style: TextStyle(
                          fontSize: 15,
                          color: Colors.grey.shade600,
                        ),
                      ),
                      if (hotel.address.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          hotel.address,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            if (hotel.latitude != null && hotel.longitude != null) ...[
              LocationMap(
                latitude: hotel.latitude!,
                longitude: hotel.longitude!,
                title: hotel.name,
              ),
              const SizedBox(height: 20),
            ],

            _buildStayCard(),

            const SizedBox(height: 20),

            _buildRoomDetailsCard(),

            if (hotel.facilities.isNotEmpty) ...[
              const SizedBox(height: 20),
              _buildFacilitiesCard(),
            ],

            const SizedBox(height: 20),

            _buildPriceCard(),

            const SizedBox(height: 20),

            _buildIntercityTransferCard(),

            const SizedBox(height: 20),

            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: isDeleting ? null : _changeHotel,
                    child: const Text('Change hotel'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    onPressed: isDeleting || hotel.rateOptions.isEmpty
                        ? null
                        : _changeRoom,
                    child: const Text('Change room'),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: isDeleting
                    ? null
                    : () {
                        // Booking will be connected later.
                      },
                icon: const Icon(Icons.open_in_new),
                label: const Text('Book this hotel'),
              ),
            ),

            const SizedBox(height: 12),

            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: isDeleting ? null : _deleteHotel,
                icon: isDeleting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.delete_outline),
                label: Text(isDeleting ? 'Deleting...' : 'Delete hotel'),
                style: OutlinedButton.styleFrom(foregroundColor: Colors.red),
              ),
            ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
