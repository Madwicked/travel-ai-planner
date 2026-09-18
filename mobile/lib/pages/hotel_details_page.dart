import 'package:flutter/material.dart';

import '../models/hotel.dart';

class HotelDetailsPage extends StatelessWidget {
  final Hotel hotel;

  const HotelDetailsPage({super.key, required this.hotel});

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

  String _formatDate(DateTime date) {
    return '${date.day.toString().padLeft(2, '0')}.'
        '${date.month.toString().padLeft(2, '0')}.'
        '${date.year}';
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
            // =========================
            // HEADER
            // =========================
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

            // =========================
            // STAY
            // =========================
            _buildStayCard(),

            const SizedBox(height: 20),

            // =========================
            // SELECTED OPTION
            // =========================
            _buildSelectedRateCard(),

            if (hotel.rateOptions.isNotEmpty) const SizedBox(height: 20),

            // =========================
            // PRICE
            // =========================
            _buildPriceCard(),

            const SizedBox(height: 20),

            // =========================
            // BOOK
            // =========================
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  // Booking will be connected later.
                },
                icon: const Icon(Icons.open_in_new),
                label: const Text('Book this hotel'),
              ),
            ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
