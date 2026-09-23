import 'package:flutter/material.dart';

import 'transport_search_page.dart';

class TransportTypeSelectionPage extends StatelessWidget {
  final Map<String, dynamic> trip;

  const TransportTypeSelectionPage({super.key, required this.trip});

  @override
  Widget build(BuildContext context) {
    final isReturnTransport = trip['return_transport'] == true;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          isReturnTransport
              ? 'Choose return transport'
              : 'Choose outbound transport',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'How do you want to travel?',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            Text(
              isReturnTransport
                  ? 'Choose your transport type for the return trip.'
                  : 'Choose your transport type for the outbound trip.',
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),

            const SizedBox(height: 24),

            _buildTransportTypeCard(
              context: context,
              type: 'Flight',
              icon: Icons.flight,
            ),

            _buildTransportTypeCard(
              context: context,
              type: 'Train',
              icon: Icons.train,
            ),

            _buildTransportTypeCard(
              context: context,
              type: 'Bus',
              icon: Icons.directions_bus,
            ),

            _buildTransportTypeCard(
              context: context,
              type: 'Transfer',
              icon: Icons.directions_car,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTransportTypeCard({
    required BuildContext context,
    required String type,
    required IconData icon,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) =>
                  TransportSearchPage(trip: trip, transportType: type),
            ),
          );

          if (!context.mounted) {
            return;
          }

          if (result != null) {
            Navigator.pop(context, result);
          }
        },
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: Colors.blue, size: 30),
              ),

              const SizedBox(width: 16),

              Expanded(
                child: Text(
                  type,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),

              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}
