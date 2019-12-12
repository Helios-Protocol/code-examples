# Requirements:
# pip install helios-web3
# pip install py-helios-solc
#
from helios_web3 import HeliosWeb3 as Web3
from helios_web3 import IPCProvider, WebsocketProvider
from helios_web3.utils.block_creation import prepare_and_sign_block

from helios_solc import install_solc, compile_files

W3_TX_DEFAULTS = {'gas': 0, 'gasPrice': 0, 'chainId': 0}

#
# First we compile our solidity file.
#

# First install the solidity binary v100.5.12 and above is helios solc
from hvm.constants import CREATE_CONTRACT_ADDRESS

install_solc('v100.5.12')

# Next, compile your file. We will compile the delegated token contract
solidity_file = '../../smart_contracts/solidity/delegated_token.sol'
contract_name = 'HeliosDelegatedToken'
compiled_sol = compile_files([solidity_file])

# get the contract interface. This contains the binary, the abi etc...
contract_interface = compiled_sol['{}:{}'.format(solidity_file, contract_name)]


#
# Next, we deploy the compiled contract to the network
#

# Websocket URL for hypothesis testnet bootnode. If you change this to mainnet, make sure you change network id too.
websocket_url = 'wss://hypothesis1.heliosprotocol.io:30304'
network_id = 42

# Create web3
w3 = Web3(WebsocketProvider(websocket_url))

# Create a random private key. This must be replaced with the private key you want to use to deploy the contract
new_account = w3.hls.account.create()
private_key = new_account._key_obj

# Create the web3 contract factory
HeliosDelegatedToken = w3.hls.contract(
    abi=contract_interface['abi'],
    bytecode=contract_interface['bin']
)

# Build transaction to deploy the contract.
w3_tx1 = HeliosDelegatedToken.constructor().buildTransaction(W3_TX_DEFAULTS)


transaction = {
                'to': CREATE_CONTRACT_ADDRESS,
                'gas': 20000000, #make sure this is enough to cover deployment
                'value': 0,
                'chainId': network_id,
                'data': w3_tx1['data']
            }

# Give the transaction the correct nonce and prepare the header
signed_block, header_dict, transactions = prepare_and_sign_block(w3, private_key, [transaction])

# Send it to the network
response = w3.hls.sendRawBlock(signed_block['rawBlock'])

# Done!

