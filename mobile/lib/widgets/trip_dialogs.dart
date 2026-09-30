import 'package:flutter/material.dart';

class TripDialogs {
  static Future<bool> showAddTransferDialog(
    BuildContext context, {
    required bool isReturn,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Add transfer?'),
          content: Text(
            isReturn
                ? 'Would you like to add a transfer from your hotel to the airport?'
                : 'Would you like to add a transfer from the airport to your hotel?',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop(false);
              },
              child: const Text('Later'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.of(dialogContext).pop(true);
              },
              child: const Text('Add transfer'),
            ),
          ],
        );
      },
    );

    return result == true;
  }
}
