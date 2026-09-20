import 'package:flutter/material.dart';

import '../models/hotel.dart';

class HotelRatesPage extends StatelessWidget {
  final Hotel hotel;

  const HotelRatesPage({super.key, required this.hotel});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Choose room and meal plan',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: ListView.separated(
          padding: const EdgeInsets.all(20),
          itemCount: hotel.rateOptions.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            final rate = hotel.rateOptions[index];

            return Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () {
                  Navigator.pop(context, rate);
                },
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        rate.roomName,
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      if (rate.boardName.isNotEmpty) ...[
                        const SizedBox(height: 5),
                        Text(
                          rate.boardName,
                          style: TextStyle(color: Colors.grey.shade700),
                        ),
                      ],

                      const SizedBox(height: 12),

                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${rate.pricePerNight.toStringAsFixed(2)} '
                              '${rate.currency}/night',
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),

                          const SizedBox(width: 12),

                          Text(
                            '${rate.totalPrice.toStringAsFixed(2)} '
                            '${rate.currency}',
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 10),

                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: [
                          Chip(
                            label: Text(
                              rate.refundable ? 'Refundable' : 'Non-refundable',
                            ),
                            visualDensity: VisualDensity.compact,
                          ),

                          if (rate.taxesIncluded)
                            const Chip(
                              label: Text('Taxes included'),
                              visualDensity: VisualDensity.compact,
                            ),
                        ],
                      ),

                      if (rate.cancellationPolicies.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text(
                            'Cancellation policy available',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
