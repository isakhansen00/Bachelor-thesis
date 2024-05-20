# signals.py
import time
#import pyModeS as pms
adsb_signals = [
    "8d4a91fa58132419d7c417dc9736", "8d4a91fa9908968350648fab4342", "8d4a91fa234c14f4c71de0bc9933", "8d47875a584bb09a07d35324abb6",
    "8d4a91faea0dc7dc013c08ca9d1c", "8d4a91fa5813941995c4709b333b", "8d4a91fa9908948790709045f1fd", "8d4a91fa5813a4198dc47786f027",
    "8d4a91fa99089388506c90f75740", "8d4a91faf82300060049b8e1899f", "8d4a91fa5813d41963c49a88959c", "8d4a91fa5813e0d89dd944182af6",
    "8d4a91fa99088e8b106490561f81", "a000023eab797d1321643054efa3", "8d4a91faf82300060049b8e1899f", "8d4a91fa5813f0d883d955488d59",
    "8d4a91fa99088c8bd0649030f6e2", "8d4a91faf82300060049b8e1899f", "8d4a91faea0dc7dc013c08ca9d1c", "8d47875aea4a5866293c08f44ea9",
    "8d47875a990c6dab30bc9c8a1e47", "8d4a91faea0dc7dc013c08ca9d1c", "8d4a91fa99087f8f3060906e7f83", "8d47875a584f27d87bbe865013c5",
    "8d47875aea4a5866293c08f44ea9", "8d47875a990c6dab50bc9c459a3c", "8d47875af82100020049b8a0ad63", "8d47875a584f57d815be77b4da51",
    "8d47875a990c6dab50bc9c459a3c", "8d4a91fa99087690d058903276e1", "8d4a91fa581550d7e3d9a1d47b4a", "a8001332c5ba6925e2e45dc87581",
    "8d47875a990c6dab50c09cafd427", "8d47875a990c6dab50c09cafd427", "a00009bac5ba6b2623245e0623b6", "a00009bbc5ba6b26231c5ed6099d",
    "a00009bdca3e51f0a80000acbf74", "a80016228db0002fa0000072ac17", "8d47875aea4a5866293c08f44ea9", "a0000a10c5aa6d266354625d28bd",
    "8d47875a990c6dab70c89c9ac40e", "8d47875a585127d673be395acefd", "8d4a91fa5815a0d719d9d5b2fa91", "8d4a91fa990853965050903e6990",
    "8d47875a585157d619be2b73fa6f", "8d4a91fa234c14f4c71de0bc9933", "8d4a91faea0dc7dc013c08ca9d1c", "8d47875a990c6dab70d49c32460e",
    "8d47875af82100020049b8a0ad63", "8d47875a990c6dab90d49be816fc", "8d47875a990c6dab90d49de832d1", "8d4a91fa5815e41731c55906cd42",
    "8d47875a990c6dab90d49be816fc", "8d47875a990c6dab90d49c17c6d8", "8d47875a5851e0931bd244c64485", "8d47875aea4a58662f3c08d8b72f",
    "8d47875a2338f6b3d37820bbef0a", "8d47875a585317d48bbdf03608dd", "8d4a91fa99084e98d07c91224d20", "8d47875a990c6dab90c89cbf44d8",
    "8d47875aea4a58662f3c08d8b72f", "8d4a91fa99084a9990a4919a4f2f", "8d47875aea4a58662f3c08d8b72f", "8d47875a990c6dabb0b49befa6ce",
    "8d4a91fa5817f41561c5a7266fe2", "8d47875a5855309049d1d7bfb309", "8d47875aea4a58662f3c08d8b72f", "a0000312b7e9cd17632464a68f27",
    "8d47875ae1133200000000bf9cf2", "8d4a91fa5819441503c5b44e053b", "8d4a91fa9908409af0d4926a7344", "8d47875a990c6eabd0bc9d5575ca",
    "a8001622b849cb17634c689ef744", "8d4a91fa581960d41bda5afa5589", "8d47875a990c6eabd0c09c40cfd8", "8d4a91fa581980d3efda603e06a4",
    "8d47875a990c6eabd0c09dbf3bd1"
]



for i, signal in enumerate(adsb_signals):
    print(signal)  # or do whatever you want with the signal

# print(len(set(adsb_signals)))

# signal_counts = {}

# # Iterate over the list of signals
# for signal in adsb_signals:
#     # Increment the count for the current signal
#     signal_counts[signal] = signal_counts.get(signal, 0) + 1

# # Iterate over the dictionary to print signals that appear more than once
# for signal, count in signal_counts.items():
#     if count > 1:
#         print(f"Signal: {signal}, Count: {count}")
#         try:
#             print(pms.decoder.adsb.typecode(signal))
#         except RuntimeError:
#             print("Not a position message")

# print(pms.decoder.adsb.callsign("8d47808d990c508f40689716c8e6"))
