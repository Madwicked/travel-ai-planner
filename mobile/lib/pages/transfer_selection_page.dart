import 'package:flutter/material.dart';

import '../models/transport.dart';

class TransferSelectionPage extends StatelessWidget {
  final Map<String, dynamic> trip;
  final Transport parentTransport;

  const TransferSelectionPage({
    super.key,
    required this.trip,
    required this.parentTransport,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Choose transfer',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Choose a transfer',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Transfer options for ${parentTransport.arrivalLocation} '
              'will be available here.',
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }
}
