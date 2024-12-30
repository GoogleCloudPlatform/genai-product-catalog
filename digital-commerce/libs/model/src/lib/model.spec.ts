import { NewProduct } from './model';

describe('retailModel', () => {
  it('should work', () => {
    const product = NewProduct();

    expect(product.base.language).toEqual('EN');
  });
});
