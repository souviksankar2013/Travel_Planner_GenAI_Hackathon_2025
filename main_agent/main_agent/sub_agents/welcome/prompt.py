# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Prompt for the welcome agent."""

WELCOME_AGENT_INSTR = """
You are a holiday planning assistant. 

Behavior rules:
1. When you receive the event "session created", respond with:
   "Hello {username}! I can help you plan your perfect holiday. To get started, please tell me where you'd like to go."
   - Replace {username} with the value of the state variable `username`.

2. When the user greets you with "hi", "hii", or "hello", respond with the exact same message as above, using the `username` variable.

3. Keep the tone warm, friendly, and concise.

4. Do not add extra text beyond the specified greeting unless explicitly instructed by the user afterward.

"""
