require 'spec_helper'

# feat~rspec_describe_it_block~1
describe 'Widget' do
  it 'is buildable' do
    expect(Widget.new).to be_a(Widget)
  end
end

# feat~rspec_context_it_block~1
context 'when empty' do
  it 'has no items' do
    expect(subject).to be_empty
  end
end

# feat~rspec_context_oneliner~1
context 'when a match exists' do
  it { is_expected.to be_a_match }
end

# feat~rspec_describe_oneliner~1
describe 'a helper' do
  it { expect(helper.call).to eq(1) }
end
