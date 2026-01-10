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

ArgMin(a) = (SqlExpr(
  "(SELECT TOP 1 {arg} FROM (SELECT {arg} as arg, {value} as val) t ORDER BY val)",
  {arg: {argpod: a.arg}, value: a.value})).argpod;

ArgMax(a) = (SqlExpr(
  "(SELECT TOP 1 {arg} FROM (SELECT {arg} as arg, {value} as val) t ORDER BY val DESC)",
  {arg: {argpod: a.arg}, value: a.value})).argpod;

ArgMaxK(a, l) = SqlExpr(
  "(SELECT TOP {lim} {arg} FROM (SELECT {arg} as arg, {value} as val) t ORDER BY val DESC FOR JSON PATH)",
  {arg: a.arg, value: a.value, lim: l});

ArgMinK(a, l) = SqlExpr(
  "(SELECT TOP {lim} {arg} FROM (SELECT {arg} as arg, {value} as val) t ORDER BY val FOR JSON PATH)",
  {arg: a.arg, value: a.value, lim: l});

Array(a) = SqlExpr(
  "(SELECT {value} FROM (SELECT {value} as value, {arg} as arg) t ORDER BY arg FOR JSON PATH)",
  {arg: a.arg, value: a.value});

Fingerprint(s) = SqlExpr("CONVERT(BIGINT, HASHBYTES('MD5', {s}))", {s:});

Chr(x) = SqlExpr("CHAR({x})", {x:});

Num(a) = a;
Str(a) = a;
"""
