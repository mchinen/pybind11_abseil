# Copyright (c) 2019-2021 The Pybind Development Team. All rights reserved.
#
# All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.
"""Tests for absl pybind11 casters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import sys

from absl.testing import absltest
from absl.testing import parameterized
from dateutil import tz
import numpy as np

from pybind11_abseil.tests import absl_example


if sys.version_info.major > 2:
  DateTime = datetime.datetime
else:
  class DateTime(datetime.datetime):

    def timestamp(self):
      if self.tzinfo:
        with_tz = self
      else:
        with_tz = self.replace(tzinfo=tz.gettz())  # pylint: disable=g-tzinfo-replace
      epoch = datetime.datetime(1970, 1, 1, tzinfo=tz.tzutc())  # pylint: disable=g-tzinfo-datetime
      return (with_tz - epoch).total_seconds()


class AbslTimeTest(parameterized.TestCase):
  SECONDS_IN_DAY = 24 * 60 * 60
  POSITIVE_SECS = 3 * SECONDS_IN_DAY + 2.5
  NEGATIVE_SECS = -3 * SECONDS_IN_DAY + 2.5
  TEST_DATETIME = DateTime(2000, 1, 2, 3, 4, 5, int(5e5))
  # Linter error relevant for pytz only.
  # pylint: disable=g-tzinfo-replace
  TEST_DATETIME_UTC = TEST_DATETIME.replace(tzinfo=tz.tzutc())
  # pylint: enable=g-tzinfo-replace
  TEST_DATE = datetime.date(2000, 1, 2)

  def test_return_positive_duration(self):
    duration = absl_example.make_duration(self.POSITIVE_SECS)
    self.assertEqual(duration.days, 3)
    self.assertEqual(duration.seconds, 2)
    self.assertEqual(duration.microseconds, 5e5)

  def test_return_negative_duration(self):
    duration = absl_example.make_duration(self.NEGATIVE_SECS)
    self.assertEqual(duration.days, -3)
    self.assertEqual(duration.seconds, 2)
    self.assertEqual(duration.microseconds, 5e5)

  def test_pass_positive_duration(self):
    duration = datetime.timedelta(seconds=self.POSITIVE_SECS)
    self.assertTrue(absl_example.check_duration(duration, self.POSITIVE_SECS))

  def test_pass_negative_duration(self):
    duration = datetime.timedelta(seconds=self.NEGATIVE_SECS)
    self.assertTrue(absl_example.check_duration(duration, self.NEGATIVE_SECS))

  def test_return_datetime(self):
    secs = self.TEST_DATETIME.timestamp()
    local_tz = tz.gettz()
    # pylint: disable=g-tzinfo-datetime
    # Warning about tzinfo applies to pytz, but we are using dateutil.tz
    expected_datetime = DateTime(
        year=self.TEST_DATETIME.year,
        month=self.TEST_DATETIME.month,
        day=self.TEST_DATETIME.day,
        hour=self.TEST_DATETIME.hour,
        minute=self.TEST_DATETIME.minute,
        second=self.TEST_DATETIME.second,
        microsecond=self.TEST_DATETIME.microsecond,
        tzinfo=local_tz)
    # pylint: enable=g-tzinfo-datetime
    # datetime handling code will set the local timezone on C++ times for want
    # of a better alternative
    self.assertEqual(expected_datetime, absl_example.make_datetime(secs))

  def test_pass_date(self):
    secs = DateTime(
        self.TEST_DATE.year,
        self.TEST_DATE.month,
        self.TEST_DATE.day).timestamp()
    self.assertTrue(absl_example.check_datetime(self.TEST_DATE, secs))

  def test_pass_datetime(self):
    secs = self.TEST_DATETIME.timestamp()
    self.assertTrue(absl_example.check_datetime(self.TEST_DATETIME, secs))

  def test_pass_datetime_with_timezone(self):
    pacific_tz = tz.gettz('America/Los_Angeles')
    # pylint: disable=g-tzinfo-datetime
    # Warning about tzinfo applies to pytz, but we are using dateutil.tz
    dt_with_tz = DateTime(
        year=2020, month=2, day=1, hour=20, tzinfo=pacific_tz)
    # pylint: enable=g-tzinfo-datetime
    secs = dt_with_tz.timestamp()
    self.assertTrue(absl_example.check_datetime(dt_with_tz, secs))

  def test_pass_datetime_dst_with_timezone(self):
    pacific_tz = tz.gettz('America/Los_Angeles')
    # pylint: disable=g-tzinfo-datetime
    dst_end = DateTime(2020, 11, 1, 2, 0, 0, tzinfo=pacific_tz)
    # pylint: enable=g-tzinfo-datetime
    secs = dst_end.timestamp()
    self.assertTrue(absl_example.check_datetime(dst_end, secs))

  def test_pass_datetime_dst(self):
    dst_end = DateTime(2020, 11, 1, 2, 0, 0)
    secs = dst_end.timestamp()
    self.assertTrue(absl_example.check_datetime(dst_end, secs))

  @parameterized.named_parameters(('before', -1),
                                  ('flip', 0),
                                  ('after', 1))
  def test_dst_datetime_from_timestamp(self, offs):
    secs_flip = 1604224799  # 2020-11-01T02:00:00-08:00
    secs = secs_flip + offs
    time_utc = DateTime.fromtimestamp(secs, tz.tzutc())
    time_local_aware = time_utc.astimezone(tz.gettz())
    time_local_naive = time_local_aware.replace(tzinfo=None)
    for time in (time_utc, time_local_aware, time_local_naive):
      self.assertTrue(absl_example.check_datetime(time, secs))

  def test_pass_datetime_pre_unix_epoch(self):
    dt = DateTime(1969, 7, 16, 10, 56, 7, microsecond=140)
    secs = dt.timestamp()
    self.assertTrue(absl_example.check_datetime(dt, secs))

  def test_return_civilsecond(self):
    # We need to use a timezone aware datetime here, otherwise
    # datetime.timestamp converts to localtime. UTC is chosen as the convention
    # in the test cases.
    truncated = self.TEST_DATETIME.replace(microsecond=0)
    self.assertEqual(
        truncated,
        absl_example.make_civilsecond(self.TEST_DATETIME_UTC.timestamp()))

  def test_pass_datetime_as_civilsecond(self):
    truncated = self.TEST_DATETIME_UTC.replace(microsecond=0)
    self.assertTrue(
        absl_example.check_civilsecond(self.TEST_DATETIME,
                                       truncated.timestamp()))

  def test_return_civilminute(self):
    truncated = self.TEST_DATETIME.replace(second=0, microsecond=0)
    self.assertEqual(
        truncated,
        absl_example.make_civilminute(self.TEST_DATETIME_UTC.timestamp()))

  def test_pass_datetime_as_civilminute(self):
    truncated = self.TEST_DATETIME_UTC.replace(second=0, microsecond=0)
    self.assertTrue(
        absl_example.check_civilminute(self.TEST_DATETIME,
                                       truncated.timestamp()))

  def test_return_civilhour(self):
    truncated = self.TEST_DATETIME.replace(minute=0, second=0, microsecond=0)
    self.assertEqual(
        truncated,
        absl_example.make_civilhour(self.TEST_DATETIME_UTC.timestamp()))

  def test_pass_datetime_as_civilhour(self):
    truncated = self.TEST_DATETIME_UTC.replace(
        minute=0, second=0, microsecond=0)
    self.assertTrue(
        absl_example.check_civilhour(self.TEST_DATETIME, truncated.timestamp()))

  def test_return_civilday(self):
    truncated = self.TEST_DATETIME.replace(
        hour=0, minute=0, second=0, microsecond=0)
    self.assertEqual(
        truncated,
        absl_example.make_civilday(self.TEST_DATETIME_UTC.timestamp()))

  def test_pass_datetime_as_civilday(self):
    truncated = self.TEST_DATETIME_UTC.replace(
        hour=0, minute=0, second=0, microsecond=0)
    self.assertTrue(
        absl_example.check_civilday(self.TEST_DATETIME, truncated.timestamp()))

  def test_return_civilmonth(self):
    truncated = self.TEST_DATETIME.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    self.assertEqual(
        truncated,
        absl_example.make_civilmonth(self.TEST_DATETIME_UTC.timestamp()))

  def test_pass_datetime_as_civilmonth(self):
    truncated = self.TEST_DATETIME_UTC.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    self.assertTrue(
        absl_example.check_civilmonth(self.TEST_DATETIME,
                                      truncated.timestamp()))

  def test_return_civilyear(self):
    truncated = self.TEST_DATETIME.replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    self.assertEqual(
        truncated,
        absl_example.make_civilyear(self.TEST_DATETIME_UTC.timestamp()))

  def test_pass_datetime_as_civilyear(self):
    truncated = self.TEST_DATETIME_UTC.replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    self.assertTrue(
        absl_example.check_civilyear(self.TEST_DATETIME, truncated.timestamp()))


class AbslSpanTest(parameterized.TestCase):

  def test_return_span(self):
    values = [1, 2, 3, 4]
    container = absl_example.VectorContainer()
    self.assertSequenceEqual(container.make_span(values), values)

  @parameterized.named_parameters(('list', [2, 4, 6]), ('tuple', (1, 3, 5, 7)),
                                  ('numpy', np.array([7, 8, 9])))
  def test_pass_span_from(self, values):
    # Pass values twice- one will be converted to a span, the other to a vector
    # (which is known to work), and then they will be compared.
    self.assertTrue(absl_example.check_span(values, values))

  def test_span_with_pointers(self):
    objs = [absl_example.ObjectForSpan(3), absl_example.ObjectForSpan(5)]
    self.assertEqual(absl_example.SumObjectPointersSpan(objs), 8)


class AbslNonConstSpanTest(parameterized.TestCase):
  _VECTOR_SIZE = 5
  _CHECKED_VALUE_DOUBLE = 3.14
  _CHECKED_VALUE_INT = 43

  @parameterized.named_parameters(
      ('double', np.zeros(_VECTOR_SIZE, dtype=np.float),
       'fill_non_const_span_double', _CHECKED_VALUE_DOUBLE),
      ('int', np.zeros(_VECTOR_SIZE, dtype=np.int32),
       'fill_non_const_span_int', _CHECKED_VALUE_INT))
  def test_span_as_out_parameter(self, vector, function_name, value):
    span_test_function = getattr(absl_example, function_name)
    span_test_function(value, vector)
    for e in vector:
      self.assertEqual(e, value)

  @parameterized.named_parameters(
      ('double', np.zeros((_VECTOR_SIZE, _VECTOR_SIZE), dtype=np.float),
       'fill_non_const_span_double', _CHECKED_VALUE_DOUBLE),
      ('int', np.zeros(
          (_VECTOR_SIZE, _VECTOR_SIZE),
          dtype=np.int32), 'fill_non_const_span_int', _CHECKED_VALUE_INT))
  def test_fails_for_wrong_numpy_dimensions(self, vector, function_name, value):
    span_test_function = getattr(absl_example, function_name)
    with self.assertRaises(TypeError):
      span_test_function(value, vector)

  @parameterized.named_parameters(
      ('double', np.zeros(_VECTOR_SIZE, dtype=np.float),
       'fill_non_const_span_double', _CHECKED_VALUE_DOUBLE),
      ('int', np.zeros(_VECTOR_SIZE, dtype=np.int32),
       'fill_non_const_span_int', _CHECKED_VALUE_INT))
  def test_fails_for_non_writable_numpy_vector(self, vector, function_name,
                                               value):
    span_test_function = getattr(absl_example, function_name)
    vector.flags.writeable = False
    with self.assertRaises(TypeError):
      span_test_function(value, vector)

  @parameterized.named_parameters(
      ('double', [0.0] * _VECTOR_SIZE, 'fill_non_const_span_double',
       _CHECKED_VALUE_DOUBLE), ('int', [0] * _VECTOR_SIZE,
                                'fill_non_const_span_int', _CHECKED_VALUE_INT))
  def test_fails_for_non_numpy_vector(self, vector, function_name, value):
    span_test_function = getattr(absl_example, function_name)
    with self.assertRaises(TypeError):
      span_test_function(value, vector)

  @parameterized.named_parameters(
      ('double', np.zeros(_VECTOR_SIZE, dtype=np.float),
       'fill_non_const_span_double', _CHECKED_VALUE_DOUBLE),
      ('int', np.zeros(_VECTOR_SIZE, dtype=np.int32),
       'fill_non_const_span_int', _CHECKED_VALUE_INT))
  def test_fails_for_non_contiguous_numpy_vector(self, vector, function_name,
                                                 value):
    span_test_function = getattr(absl_example, function_name)
    # View with step > 1 is a way to get non-contiguous memory.
    v_strided = vector[::2]
    with self.assertRaises(TypeError):
      span_test_function(value, v_strided)

  def test_fails_for_not_supported_type(self):
    # Checking only the floating version of the function as there is a type
    # mismatch in any case.
    vector = np.zeros(AbslNonConstSpanTest._VECTOR_SIZE, dtype=np.unicode_)
    with self.assertRaises(TypeError):
      absl_example.fill_non_const_span_double(
          AbslNonConstSpanTest._CHECKED_VALUE_DOUBLE, vector)

  def test_const_span_wrapper(self):
    # Test that we can use non-const Span as wrapper for const Span to avoid
    # copying data.
    values = [1, 2, 3, 4]
    vector = np.array(values, dtype=np.int32)
    self.assertTrue(absl_example.check_span_no_copy(vector, values))


class AbslStringViewTest(absltest.TestCase):
  TEST_STRING = 'test string!'

  def test_return_view(self):
    container = absl_example.StringContainer()
    self.assertSequenceEqual(
        container.make_string_view(self.TEST_STRING), self.TEST_STRING)

  def test_pass_string_view(self):
    self.assertTrue(
        absl_example.check_string_view(self.TEST_STRING, self.TEST_STRING))


class AbslFlatHashMapTest(absltest.TestCase):

  def test_return_map(self):
    keys_and_values = [(1, 2), (3, 4), (5, 6)]
    expected = dict(keys_and_values)
    self.assertEqual(expected, absl_example.make_map(keys_and_values))

  def test_pass_map(self):
    expected = [(10, 20), (30, 40)]
    self.assertTrue(absl_example.check_map(dict(expected), expected))


class AbslFlatHashSetTest(absltest.TestCase):

  def test_return_set(self):
    values = [1, 3, 7, 5]
    expected = set(values)
    self.assertEqual(expected, absl_example.make_set(values))

  def test_pass_set(self):
    expected = [10, 20, 30, 40]
    self.assertTrue(absl_example.check_set(set(expected), expected))


class AbslOptionalTest(absltest.TestCase):

  def test_pass_default_nullopt(self):
    self.assertTrue(absl_example.check_optional())

  def test_pass_value(self):
    self.assertTrue(absl_example.check_optional(5, True, 5))

  def test_pass_none(self):
    self.assertTrue(absl_example.check_optional(None, False))

  def test_return_value(self):
    self.assertEqual(absl_example.make_optional(5), 5)

  def test_return_none(self):
    self.assertIsNone(absl_example.make_optional())


class AbslVariantTest(absltest.TestCase):

  def test_variant(self):
    assert absl_example.VariantToInt(absl_example.A(3)) == 3
    assert absl_example.VariantToInt(absl_example.B(5)) == 5

    for identity_f, should_be_equal in [(absl_example.Identity, True),
                                        (absl_example.IdentityWithCopy, False)]:
      objs = [absl_example.A(3), absl_example.B(5)]
      vector = identity_f(objs)
      self.assertLen(vector, 2)
      self.assertIsInstance(vector[0], absl_example.A)
      self.assertEqual(vector[0].a, 3)
      self.assertIsInstance(vector[1], absl_example.B)
      self.assertEqual(vector[1].b, 5)
      if should_be_equal:
        self.assertEqual(objs, vector)
      else:
        self.assertNotEqual(objs, vector)


if __name__ == '__main__':
  absltest.main()
