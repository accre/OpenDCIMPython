"""
Audits are functions that consider the state of the OpenDCIM database
as a whole against policies or other sources of information, and
ensure that the information in the database matches the policy or
information source.

All reports return a dict with three fields: a ``result`` field with
a value of ``OK``, ``Repaired``, or ``Error``; an ``errors`` field
with a list of problems that could not or were not repaired, and
a ``repairs`` field with a list of repairs performed.
"""
from collections import defaultdict

from dcim.client import DCIMClient
from dcim.util import normalize_label, VALID_LABEL_RE


class DCIMAudit:
    """
    Base class for all audits setting up attributes to store error
    and repair messages, and handle making the final report.

    Audits are performed by calling the ``perform`` method which is
    defined in all subclasses, and should return the result of the
    ``_complete`` method.
    """
    def __init__(self):
        self.errors = []
        self.repairs = []

    def perform(self):
        """
        Perform a noop audit. This method should be overridden in
        subclasses.

        :returns: Audit report
        :rtype: dict
        """
        return self._complete()

    def _complete(self):
        """
        Compile a result dict from the errors and repairs lists
        """
        result = {}
        if not (self.errors or self.repairs):
            result['result'] = 'OK'
        elif not self.errors:
            result['result'] = 'Repaired'
        else:
            result['result'] = 'Error'

        result['errors'] = self.errors
        result['repairs'] = self.repairs
        return result
        

class AuditDeviceLabels(DCIMAudit):
    """
    Ensure that all device labels follow the policy of containing only
    characters a-z, 0-9, and non-repeated ``-``s. In addition, check for
    any duplicate labels.
    """
    def perform(self, repair=False):
        """
        Check all devices and list any that do not follow the valid label
        policy of containing only a-z, 0-9, and non-repeated ``-``s. If
        ``repair`` is set to True, change labels to follow the policy
        if possible and mark an error otherwise. Find duplicate labels and
        list these as errors.

        :param bool repair: If True, try to modify device labels to follow
            policy
        :returns: Audit report
        :rtype: dict
        """
        self.client = DCIMClient()
        self.found_labels = defaultdict(list)

        devs = self.client.get_all_devices()
        for device in devs:
            self._check_device_label(device, repair=repair)

        for label in self.found_labels:
            if len(self.found_labels[label]) > 1:
                self.errors.append(
                    'Duplicate label "{}" for device IDs: {}'
                    .format(label, self.found_labels[label])
                )

        # clear found_labels for subsequent uses of the perform method
        self.found_labels = defaultdict(list)

        return self._complete()

    def _check_device_label(self, device, repair=False):
        """audit the label of a single specified device"""
        label = device['Label']
        devid = device['DeviceID']

        if VALID_LABEL_RE.search(label):
            self.found_labels[label].append(devid)
        elif repair:
            try:
                new_label = normalize_label(label)
                self.client.update_device_by_id(devid, {'Label': new_label})
                self.found_labels[new_label].append(devid)
                self.repairs.append(
                    'Modified device label for {}, "{}" --> "{}"'
                    .format(devid, label, new_label)
                )
            except ValueError:
                self.found_labels[label].append(devid)
                self.errors.append(
                    'Invalid and uncorrectable label "{}" for device {}'
                    .format(label, devid)
                )
        else:
            self.found_labels[label].append(devid)
            self.errors.append(
                'Invalid label "{}" for device {}'
                .format(label, devid)
            )
