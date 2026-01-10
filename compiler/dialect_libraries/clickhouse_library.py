#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

library = """
->(left:, right:) = {arg: left, value: right};
`=`(left:, right:) = right :- left == right;

# ClickHouse has native argMin/argMax aggregate functions
ArgMin(a) = SqlExpr("argMin({arg}, {value})",
                    {arg: a.arg, value: a.value});

ArgMax(a) = SqlExpr("argMax({arg}, {value})",
                    {arg: a.arg, value: a.value});

# For top-K, use groupArray with arraySort
ArgMaxK(a, l) = SqlExpr(
  "arrayMap(x -> tupleElement(x, 1), arraySlice(arrayReverseSort(x -> tupleElement(x, 2), groupArray(tuple({arg}, {value}))), 1, {lim}))",
  {arg: a.arg, value: a.value, lim: l});

ArgMinK(a, l) = SqlExpr(
  "arrayMap(x -> tupleElement(x, 1), arraySlice(arraySort(x -> tupleElement(x, 2), groupArray(tuple({arg}, {value}))), 1, {lim}))",
  {arg: a.arg, value: a.value, lim: l});

# Array aggregation with ordering
Array(a) = SqlExpr(
  "arrayMap(x -> tupleElement(x, 1), arraySort(x -> tupleElement(x, 2), groupArray(tuple({value}, {arg}))))",
  {arg: a.arg, value: a.value});

# Fingerprint using cityHash64
Fingerprint(s) = SqlExpr("cityHash64({s})", {s:});

# Character function
Chr(x) = SqlExpr("char({x})", {x:});

Num(a) = a;
Str(a) = a;
"""
